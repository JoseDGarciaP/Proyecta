"""Texto que representa a cada entidad al calcular su vector."""

import re
import unicodedata

from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario


def _unir(*partes: str) -> str:
    return ". ".join(p.strip() for p in partes if p and p.strip())


def proyecto(p: Proyecto) -> str:
    return _unir(p.titulo, p.resumen, p.descripcion, f"Área: {p.area.nombre}",
                 "Etiquetas: " + ", ".join(p.etiquetas) if p.etiquetas else "",
                 f"Necesidades: {p.necesidades}" if p.necesidades else "")


def necesidades(p: Proyecto) -> str:
    """Lo que el proyecto busca en un colaborador."""
    return _unir(p.necesidades, ", ".join(p.etiquetas), p.area.nombre, "" if p.necesidades else p.resumen)


def oportunidad(o: Oportunidad) -> str:
    return _unir(o.titulo, o.entidad, o.descripcion, "Áreas: " + ", ".join(a.nombre for a in o.areas) if o.areas else "")


def usuario(u: Usuario) -> str:
    return _unir(u.programa or "", "Habilidades: " + ", ".join(u.habilidades) if u.habilidades else "",
                 "Intereses: " + ", ".join(u.intereses) if u.intereses else "", u.bio or "")


VACIAS = set(
    "de la el en y a los las del se por con para un una su al es lo como mas más o sus que "
    "este esta estos estas entre sobre sin ser son desde hasta the and of for to in".split()
)


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return sin_tildes


def palabras(texto: str) -> set[str]:
    """Palabras con significado, sin tildes ni plurales simples (para la similitud léxica y las razones)."""
    salida = set()
    for w in re.findall(r"[a-z0-9]+", normalizar(texto)):
        if len(w) < 3 or w in VACIAS:
            continue
        if len(w) > 4 and w.endswith("es"):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s"):
            w = w[:-1]
        salida.add(w)
    return salida
