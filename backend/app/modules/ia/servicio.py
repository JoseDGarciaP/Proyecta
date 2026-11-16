"""Resumen de proyectos, diagnóstico de formulación, recomendación de oportunidades y borrador de postulación.

El texto lo redacta el proveedor elegido en IA_PROVEEDOR:
  * ollama: modelo local y gratuito (por defecto).
  * groq: API en línea con capa gratuita (para el servidor), requiere GROQ_API_KEY.
  * anthropic: Claude, requiere ANTHROPIC_API_KEY.
  * reglas: sin modelo.
Si el proveedor no responde, se usa la heurística y la respuesta se marca como simulada.

La recomendación es explicable: cada sugerencia dice por qué se hace. Cuando hay modelo de
embeddings, la similitud semántica entre proyecto y oportunidad pesa un 30 % del puntaje.
"""

import json
import uuid
from datetime import date

import httpx

from app.core.config import get_settings
from app.modules.ia.schemas import Recomendacion, RespuestaAnalisis, RespuestaPitch
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.schemas import ProyectoSalida

API_URL = "https://api.anthropic.com/v1/messages"
SOLO_SEMANTICA = 0.5


def puntuar(
    proyecto: Proyecto,
    oportunidades: list[Oportunidad],
    limite: int = 3,
    semantica: dict[uuid.UUID, float] | None = None,
) -> list[Recomendacion]:
    """Afinidad: área (0.5) + ODS en común (0.2) + etiquetas (0.15) + vigencia (0.15). Solo oportunidades abiertas.

    Con `semantica` (similitud 0–1 por oportunidad) el puntaje es 70 % reglas + 30 % similitud.
    """
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

        similitud = (semantica or {}).get(op.id, 0.0)
        # Sin coincidencias de reglas, solo se sugiere si el parecido semántico es alto.
        if similitud >= (0.3 if razones else SOLO_SEMANTICA):
            puntaje = 0.7 * puntaje + 0.3 * similitud
            razones.append(f"su descripción se parece a la del proyecto ({round(similitud * 100)} %)")

        if razones:
            razones.append(f"sigue abierta hasta el {op.cierra_en.isoformat()}")
            salida.append(Recomendacion(
                oportunidad_id=op.id,
                titulo=op.titulo,
                puntaje=round(puntaje, 2),
                razon="Se sugiere porque " + ", ".join(razones[:-1]) + " y " + razones[-1] + ".",
            ))

    return sorted(salida, key=lambda r: r.puntaje, reverse=True)[:limite]


def diagnosticar_proyecto(proyecto: Proyecto) -> tuple[list[str], list[str]]:
    """Evalúa la madurez de la ficha del proyecto y devuelve (fortalezas, pasos_sugeridos)."""
    fortalezas: list[str] = []
    pasos: list[str] = []

    if proyecto.ods:
        fortalezas.append(f"Alineado con {len(proyecto.ods)} ODS ({', '.join(f'ODS {o.id}' for o in sorted(proyecto.ods, key=lambda x: x.id))}).")
    else:
        pasos.append("Asociar al menos un Objetivo de Desarrollo Sostenible (ODS) para mejorar el cruce con convocatorias.")

    if len(proyecto.descripcion.strip()) >= 80:
        fortalezas.append("Cuenta con una descripción técnica detallada del alcance.")
    else:
        pasos.append("Ampliar la descripción del proyecto explicando metodología, población objetivo y resultados esperados.")

    if proyecto.necesidades.strip():
        fortalezas.append("Define explícitamente qué perfiles o apoyos necesita sumar.")
    else:
        pasos.append("Detallar en «Lo que necesita» las habilidades, equipos o financiación requeridos para atraer colaboradores.")

    if proyecto.actores:
        fortalezas.append(f"Articulado con {len(proyecto.actores)} actor(es) externo(s) o institucional(es).")
    else:
        pasos.append("Vincular al menos un actor aliado (universidad, empresa, estado o comunidad) para respaldar la iniciativa.")

    if len(proyecto.etiquetas) >= 2:
        fortalezas.append(f"Etiquetado temático claro ({', '.join(proyecto.etiquetas[:4])}).")
    else:
        pasos.append("Agregar al menos 3 etiquetas clave para potenciar la búsqueda semántica y las recomendaciones.")

    if proyecto.presupuesto > 0 and proyecto.fecha_fin:
        fortalezas.append("Presupuesto estimado y horizonte de cierre definidos.")
    elif proyecto.presupuesto == 0:
        pasos.append("Estimar un presupuesto referencial en COP para facilitar la postulación a fondos de financiación.")

    return fortalezas[:4], pasos[:4]


def resumen_heuristico(proyecto: Proyecto) -> str:
    return (
        f"{proyecto.titulo} es una iniciativa del área de {proyecto.area.nombre} liderada por "
        f"{proyecto.lider or 'un equipo de la plataforma'}, con un avance del {proyecto.avance}%. "
        f"{proyecto.resumen} Participan {len(proyecto.equipo)} integrante(s) y "
        f"{len(proyecto.actores)} actor(es) articulado(s)."
    )


def _prompt(proyecto: Proyecto) -> str:
    datos = ProyectoSalida.de(proyecto).model_dump(mode="json", exclude={"id", "creado_por", "actores", "creado_en"})
    # Sin campos vacíos: evita que el modelo escriba cosas como «presupuesto de $0».
    datos = {k: v for k, v in datos.items() if v not in ("", [], None, 0)}
    return (
        "Redacta en español un resumen ejecutivo de máximo 60 palabras del siguiente "
        "proyecto universitario. Sé concreto, sin adjetivos promocionales. "
        "Responde solo con el resumen.\n\n"
        + json.dumps(datos, ensure_ascii=False, indent=2)
    )


def _prompt_pitch(proyecto: Proyecto, oportunidad: Oportunidad) -> str:
    datos_proy = {
        "titulo": proyecto.titulo,
        "area": proyecto.area.nombre,
        "estado": proyecto.estado.value,
        "avance_pct": proyecto.avance,
        "resumen": proyecto.resumen,
        "descripcion": proyecto.descripcion,
        "necesidades": proyecto.necesidades,
        "ods": [f"ODS {o.id}: {o.nombre}" for o in proyecto.ods],
        "etiquetas": proyecto.etiquetas,
    }
    datos_op = {
        "titulo": oportunidad.titulo,
        "entidad": oportunidad.entidad,
        "tipo": oportunidad.tipo.value,
        "descripcion": oportunidad.descripcion,
        "areas": [a.nombre for a in oportunidad.areas],
        "ods": [f"ODS {o.id}" for o in oportunidad.ods],
    }
    return (
        "Redacta en español una nota de postulación persuasiva y concreta (entre 70 y 120 palabras) "
        "en primera persona plural («Nuestro equipo…») explicando por qué el siguiente proyecto "
        "universitario encaja con la convocatoria indicada, qué problema resuelve, en qué etapa está "
        "y cómo aprovecharía el apoyo. No uses saludos formales ni encabezados; responde solo con el texto.\n\n"
        f"PROYECTO:\n{json.dumps(datos_proy, ensure_ascii=False, indent=2)}\n\n"
        f"OPORTUNIDAD:\n{json.dumps(datos_op, ensure_ascii=False, indent=2)}"
    )


def puntos_clave_pitch(proyecto: Proyecto, oportunidad: Oportunidad) -> list[str]:
    puntos: list[str] = []
    if proyecto.area.nombre in {a.nombre for a in oportunidad.areas}:
        puntos.append(f"Coincidencia directa en el área de {proyecto.area.nombre}.")
    ods_comunes = sorted({o.id for o in proyecto.ods} & {o.id for o in oportunidad.ods})
    if ods_comunes:
        puntos.append(f"Alineación en ODS {', '.join(map(str, ods_comunes))}.")
    puntos.append(f"Estado actual: {proyecto.estado.value} ({proyecto.avance}% de avance).")
    if proyecto.necesidades.strip():
        puntos.append(f"Necesidades identificadas: {proyecto.necesidades.strip()[:90]}.")
    return puntos


def pitch_heuristico(proyecto: Proyecto, oportunidad: Oportunidad) -> str:
    ods_comunes = sorted({o.id for o in proyecto.ods} & {o.id for o in oportunidad.ods})
    frase_ods = f", aportando a los ODS {', '.join(map(str, ods_comunes))}" if ods_comunes else ""
    necesidad = (
        f" Con este apoyo buscamos cubrir: {proyecto.necesidades.strip().rstrip('.')}."
        if proyecto.necesidades.strip()
        else " El apoyo nos permitirá consolidar los entregables técnicos y validar resultados con los beneficiarios."
    )
    return (
        f"Nuestro proyecto «{proyecto.titulo}» ({proyecto.area.nombre}{frase_ods}) aborda "
        f"{proyecto.resumen[:180].rstrip('.')}. Actualmente nos encontramos en etapa de "
        f"{proyecto.estado.value} con un {proyecto.avance}% de avance y un equipo de "
        f"{max(1, len(proyecto.equipo))} integrante(s). Postulamos a «{oportunidad.titulo}» de "
        f"{oportunidad.entidad} porque existe alta afinidad temática y técnica con nuestra iniciativa."
        f"{necesidad}"
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


async def _groq(cliente: httpx.AsyncClient, prompt: str) -> str:
    """API compatible con OpenAI (chat completions)."""
    settings = get_settings()
    if not settings.groq_api_key:
        return ""
    cuerpo: dict = {
        "model": settings.groq_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_completion_tokens": 800,
    }
    if settings.groq_model.startswith("openai/gpt-oss"):
        cuerpo["reasoning_effort"] = "low"  # modelo con razonamiento: basta poco para un resumen
    respuesta = await cliente.post(
        f"{settings.groq_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
        json=cuerpo,
    )
    respuesta.raise_for_status()
    return respuesta.json()["choices"][0]["message"].get("content") or ""


PROVEEDORES = {"ollama": _ollama, "groq": _groq, "anthropic": _anthropic}

# Las pruebas reemplazan el transporte HTTP para no depender de servicios externos.
_transporte: httpx.AsyncBaseTransport | None = None


async def _pedir_modelo(prompt: str) -> str | None:
    settings = get_settings()
    proveedor = PROVEEDORES.get(settings.ia_proveedor)
    if proveedor is None:
        return None
    try:
        # Un modelo local en CPU puede tardar en cargar la primera vez.
        async with httpx.AsyncClient(timeout=settings.ia_timeout, transport=_transporte) as cliente:
            texto = (await proveedor(cliente, prompt)).strip()
            return texto or None
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return None


async def resumen_modelo(proyecto: Proyecto) -> str | None:
    return await _pedir_modelo(_prompt(proyecto))


async def analizar(
    proyecto: Proyecto, oportunidades: list[Oportunidad], semantica: dict[uuid.UUID, float] | None = None
) -> RespuestaAnalisis:
    texto = await resumen_modelo(proyecto)
    fortalezas, pasos_sugeridos = diagnosticar_proyecto(proyecto)
    return RespuestaAnalisis(
        resumen=texto or resumen_heuristico(proyecto),
        recomendaciones=puntuar(proyecto, oportunidades, semantica=semantica),
        fortalezas=fortalezas,
        pasos_sugeridos=pasos_sugeridos,
        simulado=texto is None,
    )


async def generar_pitch(proyecto: Proyecto, oportunidad: Oportunidad) -> RespuestaPitch:
    texto = await _pedir_modelo(_prompt_pitch(proyecto, oportunidad))
    return RespuestaPitch(
        pitch=texto or pitch_heuristico(proyecto, oportunidad),
        puntos_clave=puntos_clave_pitch(proyecto, oportunidad),
        simulado=texto is None,
    )
