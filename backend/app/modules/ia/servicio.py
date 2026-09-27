"""Resumen de proyectos y recomendación de oportunidades.

El resumen lo redacta el proveedor elegido en IA_PROVEEDOR:
  * ollama: modelo local y gratuito (por defecto).
  * anthropic: Claude, requiere ANTHROPIC_API_KEY.
  * reglas: sin modelo.
Si el proveedor no responde, se usa la heurística y la respuesta se marca como simulada.

La recomendación es explicable: cada sugerencia dice por qué se hace.
Más adelante se sumará similitud semántica con embeddings (pgvector).
"""

import json
from datetime import date

import httpx

from app.core.config import get_settings
from app.modules.ia.schemas import Recomendacion, RespuestaAnalisis
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.schemas import ProyectoSalida

API_URL = "https://api.anthropic.com/v1/messages"


def puntuar(proyecto: Proyecto, oportunidades: list[Oportunidad], limite: int = 3) -> list[Recomendacion]:
    """Afinidad: área (0.5) + ODS en común (0.2) + etiquetas (0.15) + vigencia (0.15). Solo oportunidades abiertas."""
    hoy = date.today()
    etiquetas = {e.lower() for e in proyecto.etiquetas}
    ods_proyecto = {o.id for o in proyecto.ods}
    salida: list[Recomendacion] = []

    for op in oportunidades:
        if op.cierra_en < hoy:
            continue
        puntaje = 0.15
        razones: list[str] = []

        if proyecto.area.nombre in {a.nombre for a in op.areas}:
            puntaje += 0.5
            razones.append(f"cubre el área de {proyecto.area.nombre}")

        comunes = sorted(ods_proyecto & {o.id for o in op.ods})
        if comunes:
            puntaje += 0.2
            razones.append("comparten el ODS " + ", ".join(str(n) for n in comunes))

        texto = f"{op.titulo} {op.entidad} {op.descripcion}".lower()
        if any(e in texto for e in etiquetas):
            puntaje += 0.15
            razones.append("coincide con las etiquetas del proyecto")

        if razones:
            razones.append(f"sigue abierta hasta el {op.cierra_en.isoformat()}")
            salida.append(Recomendacion(
                oportunidad_id=op.id,
                titulo=op.titulo,
                puntaje=round(puntaje, 2),
                razon="Se sugiere porque " + ", ".join(razones[:-1]) + " y " + razones[-1] + ".",
            ))

    return sorted(salida, key=lambda r: r.puntaje, reverse=True)[:limite]


def resumen_heuristico(proyecto: Proyecto) -> str:
    return (
        f"{proyecto.titulo} es una iniciativa del área de {proyecto.area.nombre} liderada por "
        f"{proyecto.lider or 'un equipo de la plataforma'}, con un avance del {proyecto.avance}%. "
        f"{proyecto.resumen} Participan {len(proyecto.equipo)} integrante(s) y "
        f"{len(proyecto.actores)} actor(es) articulado(s)."
    )


def _prompt(proyecto: Proyecto) -> str:
    datos = ProyectoSalida.de(proyecto).model_dump(mode="json", exclude={"id", "creado_por", "actores"})
    return (
        "Redacta en español un resumen ejecutivo de máximo 60 palabras del siguiente "
        "proyecto universitario. Sé concreto, sin adjetivos promocionales. "
        "Responde solo con el resumen.\n\n"
        + json.dumps(datos, ensure_ascii=False, indent=2)
    )


async def _ollama(cliente: httpx.AsyncClient, prompt: str) -> str:
    settings = get_settings()
    respuesta = await cliente.post(
        f"{settings.ollama_url.rstrip('/')}/api/chat",
        json={
            "model": settings.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
    )
    respuesta.raise_for_status()
    return respuesta.json()["message"]["content"]


async def _anthropic(cliente: httpx.AsyncClient, prompt: str) -> str:
    settings = get_settings()
    if not settings.anthropic_api_key:
        return ""
    respuesta = await cliente.post(
        API_URL,
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.anthropic_model,
            "max_tokens": 400,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    respuesta.raise_for_status()
    return "".join(b.get("text", "") for b in respuesta.json().get("content", []))


PROVEEDORES = {"ollama": _ollama, "anthropic": _anthropic}

# Las pruebas reemplazan el transporte HTTP para no depender de servicios externos.
_transporte: httpx.AsyncBaseTransport | None = None


async def resumen_modelo(proyecto: Proyecto) -> str | None:
    settings = get_settings()
    proveedor = PROVEEDORES.get(settings.ia_proveedor)
    if proveedor is None:
        return None
    try:
        # Un modelo local en CPU puede tardar en cargar la primera vez.
        async with httpx.AsyncClient(timeout=settings.ia_timeout, transport=_transporte) as cliente:
            texto = (await proveedor(cliente, _prompt(proyecto))).strip()
            return texto or None
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


async def analizar(proyecto: Proyecto, oportunidades: list[Oportunidad]) -> RespuestaAnalisis:
    texto = await resumen_modelo(proyecto)
    return RespuestaAnalisis(
        resumen=texto or resumen_heuristico(proyecto),
        recomendaciones=puntuar(proyecto, oportunidades),
        simulado=texto is None,
    )
