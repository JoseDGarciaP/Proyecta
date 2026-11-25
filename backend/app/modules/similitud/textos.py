"""Texto que representa a cada entidad al calcular su vector."""

import re
import unicodedata

from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario


def _unir(*partes: str) -> str:
    return ". ".join(p.strip() for p in partes if p and p.strip())


# El modelo (paraphrase-multilingual-MiniLM-L12-v2) solo lee ~128 tokens y corta el resto.
# Por eso lo que más distingue a cada entidad (título, área, etiquetas, necesidades) va primero
# y la descripción larga al final: si algo se pierde, que sea el final de la descripción.

TIPOS_OPORTUNIDAD = {"convocatoria": "Convocatoria", "financiacion": "Financiación",
                     "mentoria": "Mentoría", "infraestructura": "Infraestructura"}


def proyecto(p: Proyecto) -> str:
    return _unir(p.titulo, f"Área: {p.area.nombre}",
                 "Etiquetas: " + ", ".join(p.etiquetas) if p.etiquetas else "",
                 p.resumen,
                 f"Necesidades: {p.necesidades}" if p.necesidades else "",
                 p.descripcion)


def necesidades(p: Proyecto) -> str:
    """Lo que el proyecto busca en un colaborador."""
    return _unir(p.necesidades, ", ".join(p.etiquetas), p.area.nombre, "" if p.necesidades else p.resumen)


def oportunidad(o: Oportunidad) -> str:
    tipo = getattr(o.tipo, "value", o.tipo)
    return _unir(o.titulo, TIPOS_OPORTUNIDAD.get(tipo, ""),
                 "Áreas: " + ", ".join(a.nombre for a in o.areas) if o.areas else "",
                 o.entidad, o.descripcion)


def usuario(u: Usuario) -> str:
    """Perfil para comparar. Vacío si solo tiene el programa: con eso todos los de una carrera
    quedarían con el mismo vector y las sugerencias no dirían nada."""
    if not (u.habilidades or u.intereses or (u.bio or "").strip()):
        return ""
    return _unir("Habilidades: " + ", ".join(u.habilidades) if u.habilidades else "",
                 "Intereses: " + ", ".join(u.intereses) if u.intereses else "",
                 u.bio or "", u.programa or "")


def afinidad_proyectos(a: Proyecto, b: Proyecto) -> float:
    """Etiquetas en común entre dos proyectos (0–1): 0,5 por cada palabra compartida, máximo 2.

    El modelo da puntajes altos a cualquier par de «sistema web» o «aplicación»; las etiquetas que eligió
    cada equipo dicen de qué trata de verdad. El área no cuenta: casi todos son «Tecnología»."""
    comunes = (palabras(" ".join(a.etiquetas)) & palabras(" ".join(b.etiquetas))) - GENERICAS
    return 0.5 * min(len(comunes), 2)


# Palabras que casi todos los proyectos ponen en sus etiquetas y no dicen de qué tratan
# («aplicación móvil», «gestión», «transformación digital»…). Ya sin tildes ni plural, como las deja palabras().
GENERICAS = {
    "aplicacion", "aplicativo", "app", "movil", "web", "sistema", "plataforma", "software", "tecnologia",
    "tecnologica", "digital", "gestion", "informacion", "desarrollo", "herramienta", "transformacion",
    "innovacion", "proyecto", "ods", "uso", "servicio", "linea", "virtual", "inteligente",
}


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
