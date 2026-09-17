"""Lógica de resumen y recomendación.

Dos modos:
  * heurístico  — sin dependencias externas, siempre disponible (demo).
  * modelo      — si hay ANTHROPIC_API_KEY, pide el resumen a un modelo.
"""

from __future__ import annotations

import json
import os
from datetime import date

import httpx

from .schemas import Oportunidad, Proyecto, Recomendacion, RespuestaAnalisis

API_URL = "https://api.anthropic.com/v1/messages"


def puntuar(proyecto: Proyecto, oportunidades: list[Oportunidad]) -> list[Recomendacion]:
    """Afinidad simple: área + coincidencia de etiquetas + vigencia."""
    hoy = date.today().isoformat()
    salida: list[Recomendacion] = []

    for op in oportunidades:
        puntaje = 0.0
        razones: list[str] = []

        if proyecto.area in op.areas:
            puntaje += 0.6
            razones.append(f"cubre el área de {proyecto.area}")

        etiquetas = {e.lower() for e in proyecto.etiquetas}
        texto = f"{op.titulo} {op.entidad}".lower()
        if any(e in texto for e in etiquetas):
            puntaje += 0.25
            razones.append("coincide con las etiquetas del proyecto")

        if op.cierra_en >= hoy:
            puntaje += 0.15
            razones.append("la convocatoria sigue abierta")

        if puntaje > 0:
            salida.append(
                Recomendacion(
                    oportunidad_id=op.id,
                    titulo=op.titulo,
                    puntaje=round(puntaje, 2),
                    razon="Se sugiere porque " + " y ".join(razones) + ".",
                )
            )

    return sorted(salida, key=lambda r: r.puntaje, reverse=True)[:3]


def resumen_heuristico(proyecto: Proyecto) -> str:
    return (
        f"{proyecto.titulo} es una iniciativa del área de {proyecto.area} liderada por "
        f"{proyecto.lider or 'un equipo de la plataforma'}, con un avance del {proyecto.avance}%. "
        f"{proyecto.resumen} Participan {len(proyecto.equipo)} integrante(s) y "
        f"{len(proyecto.actores)} actor(es) articulado(s)."
    )


async def resumen_modelo(proyecto: Proyecto) -> str | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    prompt = (
        "Redacta en español un resumen ejecutivo de máximo 60 palabras del siguiente "
        "proyecto universitario. Sé concreto, sin adjetivos promocionales.\n\n"
        + json.dumps(proyecto.model_dump(), ensure_ascii=False, indent=2)
    )

    try:
        async with httpx.AsyncClient(timeout=30) as cliente:
            respuesta = await cliente.post(
                API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            respuesta.raise_for_status()
            bloques = respuesta.json().get("content", [])
            texto = "".join(b.get("text", "") for b in bloques).strip()
            return texto or None
    except (httpx.HTTPError, ValueError, KeyError):
        return None


async def analizar(proyecto: Proyecto, oportunidades: list[Oportunidad]) -> RespuestaAnalisis:
    texto = await resumen_modelo(proyecto)
    return RespuestaAnalisis(
        resumen=texto or resumen_heuristico(proyecto),
        recomendaciones=puntuar(proyecto, oportunidades),
        simulado=texto is None,
    )
