"""Informe para revisar a mano si la similitud tiene sentido con los datos reales.

Uso (en el servidor; guarda el informe en un archivo para revisarlo):
    docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec -T api \
        python -m scripts.evaluar_similitud > ~/informe-similitud.txt

Por cada proyecto muestra las oportunidades, proyectos y personas más parecidos con su puntaje, y al
final la distribución de puntajes para ver si el umbral (MINIMO) corta en un buen lugar. Las líneas con
«✓» superan el umbral (se mostrarían en la plataforma); las de «·» no. No cambia datos: solo guarda los
vectores que falten, igual que cuando alguien usa la plataforma.
"""

import statistics
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Oportunidad, Proyecto, Usuario
from app.modules.similitud import codificador, textos
from app.modules.similitud.servicio import MINIMO, _calcular
from app.modules.usuarios.models import Rol

TOP = 3


def _bloque(titulo: str, sims: dict, objetos: dict, minimo: float, nombre) -> list[float]:
    print(f"  {titulo}:")
    orden = sorted(sims.items(), key=lambda x: x[1], reverse=True)[:TOP]
    if not orden:
        print("    (sin candidatos)")
    for i, s in orden:
        print(f"    {'✓' if s >= minimo else '·'} {s:.2f}  {nombre(objetos[i])}")
    return list(sims.values())


def _distribucion(nombre: str, valores: list[float], minimo: float) -> None:
    if not valores:
        return
    v = sorted(valores)
    cuartiles = statistics.quantiles(v, n=4) if len(v) > 1 else [v[0]] * 3
    sobre = sum(x >= minimo for x in v)
    print(f"{nombre:<26} n={len(v):<5} mín={v[0]:.2f}  p25={cuartiles[0]:.2f}  mediana={cuartiles[1]:.2f}  "
          f"p75={cuartiles[2]:.2f}  máx={v[-1]:.2f}  ≥umbral={sobre} ({100 * sobre / len(v):.0f} %)")


def main() -> None:
    estado = codificador.estado()
    print(f"Embeddings: {estado}")
    with SessionLocal() as db:
        proyectos = list(db.scalars(select(Proyecto)).unique())
        oportunidades = list(db.scalars(select(Oportunidad).where(Oportunidad.archivada.is_(False))))
        activos = list(db.scalars(select(Usuario).where(Usuario.activo.is_(True), Usuario.rol != Rol.ADMIN.value)))
        usuarios = [u for u in activos if textos.usuario(u)]
        print(f"{len(proyectos)} proyectos, {len(oportunidades)} oportunidades, {len(usuarios)} perfiles con "
              f"habilidades/intereses/bio ({len(activos) - len(usuarios)} perfiles vacíos no entran a la comparación)\n")
        if not proyectos:
            print("No hay proyectos para evaluar.")
            return

        por_id = {o.id: o for o in [*proyectos, *oportunidades, *usuarios]}
        todos = {"proyecto↔oportunidad": [], "proyecto↔proyecto": [], "necesidades↔persona": []}
        metodo = "lexico"
        for p in proyectos:
            print(f"■ {p.titulo}  [{p.area.nombre}; {', '.join(p.etiquetas) or 'sin etiquetas'}]")
            sims, metodo = _calcular(db, textos.proyecto(p), "oportunidad", oportunidades, textos.oportunidad)
            todos["proyecto↔oportunidad"] += _bloque("Oportunidades", sims, por_id, MINIMO[metodo],
                                                      lambda o: f"{o.titulo} ({', '.join(a.nombre for a in o.areas)})")
            otros = [x for x in proyectos if x.id != p.id]
            sims, _ = _calcular(db, textos.proyecto(p), "proyecto", otros, textos.proyecto,
                                consulta_ref=("proyecto", p, textos.proyecto))
            todos["proyecto↔proyecto"] += _bloque("Proyectos parecidos", sims, por_id, MINIMO[metodo],
                                                   lambda o: f"{o.titulo} ({o.area.nombre})")
            sims, _ = _calcular(db, textos.necesidades(p), "usuario", usuarios, textos.usuario)
            todos["necesidades↔persona"] += _bloque("Personas", sims, por_id, MINIMO[metodo],
                                                     lambda u: f"{u.nombre}: {', '.join(u.habilidades[:4])}")
            print()

        print(f"Distribución de puntajes (método {metodo}, umbral {MINIMO[metodo]}):")
        for nombre, valores in todos.items():
            _distribucion(nombre, valores, MINIMO[metodo])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
