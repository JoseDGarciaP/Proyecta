"""Similitud entre textos: semántica con embeddings o, si no hay modelo, léxica.

`ordenar()` es la única puerta de entrada: recibe una consulta y candidatos, se asegura de que
los candidatos tengan su vector guardado (solo recalcula lo que cambió) y los devuelve ordenados.
En PostgreSQL el orden lo calcula pgvector (`<=>`, distancia coseno); en SQLite, numpy.
"""

import hashlib
import math
import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.similitud import codificador
from app.modules.similitud.models import Embedding
from app.modules.similitud.textos import palabras

Metodo = Literal["semantico", "lexico"]

# Por debajo de estos valores la coincidencia no aporta; los modelos multilingües dan ~0.1 entre textos ajenos.
MINIMO = {"semantico": 0.3, "lexico": 0.08}


@dataclass
class Resultado:
    objeto: Any
    similitud: float


def _huella(modelo: str, texto: str) -> str:
    return hashlib.sha256(f"{modelo}\n{texto}".encode()).hexdigest()


def asegurar(db: Session, entidad: str, objetos: Sequence[Any], texto: Callable[[Any], str],
             cod: codificador.Codificador) -> None:
    """Calcula y guarda los vectores que faltan o cuyo texto cambió."""
    if not objetos:
        return
    ids = [o.id for o in objetos]
    guardados = {e.entidad_id: e for e in db.scalars(
        select(Embedding).where(Embedding.entidad == entidad, Embedding.entidad_id.in_(ids)))}
    pendientes: list[tuple[Any, str, str]] = []
    for o in objetos:
        t = texto(o)
        huella = _huella(cod.nombre, t)
        actual = guardados.get(o.id)
        if actual is None or actual.huella != huella:
            pendientes.append((o, t, huella))
    if not pendientes:
        return
    vectores = cod.codificar([t for _, t, _ in pendientes])
    for (o, _, huella), vector in zip(pendientes, vectores, strict=True):
        fila = guardados.get(o.id) or Embedding(entidad=entidad, entidad_id=o.id)
        fila.modelo, fila.huella, fila.vector = cod.nombre, huella, list(map(float, vector))
        db.add(fila)
    db.commit()


def _cercanos(db: Session, entidad: str, modelo: str, consulta: list[float], ids: list[uuid.UUID]) -> dict[uuid.UUID, float]:
    filtro = (Embedding.entidad == entidad, Embedding.modelo == modelo, Embedding.entidad_id.in_(ids))
    if db.get_bind().dialect.name == "postgresql":
        distancia = Embedding.vector.cosine_distance(consulta)
        return {i: 1 - float(d) for i, d in db.execute(select(Embedding.entidad_id, distancia).where(*filtro))}
    filas = db.execute(select(Embedding.entidad_id, Embedding.vector).where(*filtro)).all()
    if not filas:
        return {}
    matriz = np.array([v for _, v in filas], dtype=float)
    q = np.array(consulta, dtype=float)
    normas = np.linalg.norm(matriz, axis=1) * (np.linalg.norm(q) or 1)
    sims = matriz @ q / np.where(normas == 0, 1, normas)
    return {i: float(s) for (i, _), s in zip(filas, sims)}


def lexica(a: str, b: str) -> float:
    """Coseno entre conjuntos de palabras: |A∩B| / √(|A|·|B|)."""
    pa, pb = palabras(a), palabras(b)
    if not pa or not pb:
        return 0.0
    return len(pa & pb) / math.sqrt(len(pa) * len(pb))


def ordenar(
    db: Session,
    consulta: str,
    entidad: str,
    candidatos: Sequence[Any],
    texto: Callable[[Any], str],
    limite: int = 5,
    consulta_ref: tuple[str, Any, Callable[[Any], str]] | None = None,
) -> tuple[list[Resultado], Metodo]:
    """Candidatos más parecidos a `consulta`, de mayor a menor similitud.

    `consulta_ref` = (entidad, objeto, texto) reutiliza el vector guardado de la consulta cuando es
    una entidad (p. ej. «proyectos similares a este»), en lugar de recalcularlo.
    """
    cod = codificador.obtener()
    if cod is None:
        metodo: Metodo = "lexico"
        sims = {c.id: lexica(consulta, texto(c)) for c in candidatos}
    else:
        metodo = "semantico"
        asegurar(db, entidad, candidatos, texto, cod)
        if consulta_ref:
            ent, obj, fn = consulta_ref
            asegurar(db, ent, [obj], fn, cod)
            vector = db.get(Embedding, (ent, obj.id)).vector
            vector = list(map(float, vector))
        else:
            vector = cod.codificar([consulta])[0]
        sims = _cercanos(db, entidad, cod.nombre, vector, [c.id for c in candidatos])
    minimo = MINIMO[metodo]
    salida = [Resultado(c, round(sims.get(c.id, 0.0), 3)) for c in candidatos]
    salida = [r for r in salida if r.similitud >= minimo]
    return sorted(salida, key=lambda r: r.similitud, reverse=True)[:limite], metodo


def similitudes(db: Session, consulta: str, entidad: str, candidatos: Sequence[Any],
                texto: Callable[[Any], str]) -> tuple[dict[uuid.UUID, float], Metodo]:
    """Similitud de todos los candidatos (sin umbral), para combinarla con otras señales."""
    resultados, metodo = ordenar(db, consulta, entidad, candidatos, texto, limite=len(candidatos) or 1)
    return {r.objeto.id: r.similitud for r in resultados}, metodo
