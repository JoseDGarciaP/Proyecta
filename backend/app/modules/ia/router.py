import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from app.core.config import get_settings
from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.models import Miembro
from app.modules.ia.schemas import RespuestaAnalisis, RespuestaSugerencias, Sugerencia, SugerenciasParaMi
from app.modules.ia.servicio import analizar, puntuar
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.router import obtener_proyecto
from app.modules.similitud import codificador, textos
from app.modules.similitud.servicio import Resultado, ordenar, similitudes
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/ia", tags=["inteligencia artificial"])


@router.get("/estado")
def estado():
    settings = get_settings()
    modelo = {"ollama": settings.ollama_model, "anthropic": settings.anthropic_model}.get(settings.ia_proveedor)
    return {"proveedor": settings.ia_proveedor, "modelo": modelo, "embeddings": codificador.estado()}


def _abiertas(db) -> list[Oportunidad]:
    return list(db.scalars(select(Oportunidad).where(Oportunidad.cierra_en >= date.today())))


def _pct(r: Resultado) -> str:
    return f"{round(r.similitud * 100)} %"


def _comunes(a: str, b: str, maximo: int = 4) -> list[str]:
    """Términos del texto `b` que aparecen en `a`, para explicar la coincidencia."""
    pa = textos.palabras(a)
    return [t for t in dict.fromkeys(b.split(", ")) if t and textos.palabras(t) & pa][:maximo]


def _semantica(db, proyecto: Proyecto, oportunidades: list[Oportunidad]) -> dict[uuid.UUID, float] | None:
    """Similitud proyecto↔oportunidades, solo con embeddings: la léxica ya la cubre la regla de etiquetas."""
    if codificador.obtener() is None:
        return None
    return similitudes(db, textos.proyecto(proyecto), "oportunidad", oportunidades, textos.oportunidad)[0]


@router.post("/proyectos/{proyecto_id}/analisis", response_model=RespuestaAnalisis)
async def analizar_proyecto(proyecto_id: uuid.UUID, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    oportunidades = _abiertas(db)
    semantica = _semantica(db, proyecto, oportunidades)
    return await analizar(proyecto, oportunidades, semantica)


@router.get("/proyectos/{proyecto_id}/similares", response_model=RespuestaSugerencias)
def proyectos_similares(proyecto_id: uuid.UUID, db: DbSession, limite: int = Query(default=4, le=20)):
    """Proyectos parecidos: posibles duplicados o equipos con quienes articularse."""
    proyecto = obtener_proyecto(db, proyecto_id)
    otros = list(db.scalars(select(Proyecto).where(Proyecto.id != proyecto.id)).unique())
    resultados, metodo = ordenar(db, textos.proyecto(proyecto), "proyecto", otros, textos.proyecto, limite,
                                 consulta_ref=("proyecto", proyecto, textos.proyecto))
    return RespuestaSugerencias(metodo=metodo, resultados=[
        Sugerencia(
            id=r.objeto.id, tipo="proyecto", titulo=r.objeto.titulo, detalle=f"{r.objeto.area.nombre} · {r.objeto.lider}",
            similitud=r.similitud,
            razon=f"Parecido en un {_pct(r)}" + (" y del mismo área." if r.objeto.area_id == proyecto.area_id else "."),
        )
        for r in resultados
    ])


@router.get("/proyectos/{proyecto_id}/colaboradores", response_model=RespuestaSugerencias)
def colaboradores_sugeridos(proyecto_id: uuid.UUID, db: DbSession, _: UsuarioActual, limite: int = Query(default=5, le=20)):
    """Personas cuyo perfil (habilidades, intereses, programa) encaja con lo que el proyecto necesita."""
    proyecto = obtener_proyecto(db, proyecto_id)
    ya = {m for m in db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id))}
    ya.add(proyecto.creado_por_id)
    candidatos = [u for u in db.scalars(select(Usuario).where(Usuario.activo.is_(True), Usuario.rol != Rol.ADMIN))
                  if u.id not in ya and textos.usuario(u)]
    consulta = textos.necesidades(proyecto)
    resultados, metodo = ordenar(db, consulta, "usuario", candidatos, textos.usuario, limite)
    salida = []
    for r in resultados:
        u: Usuario = r.objeto
        comunes = _comunes(consulta, ", ".join(u.habilidades + u.intereses))
        razon = f"Su perfil coincide en un {_pct(r)} con lo que busca el proyecto"
        salida.append(Sugerencia(
            id=u.id, tipo="usuario", titulo=u.nombre, detalle=u.programa or u.rol.value, similitud=r.similitud,
            razon=razon + (f": {', '.join(comunes)}." if comunes else "."),
        ))
    return RespuestaSugerencias(metodo=metodo, resultados=salida)


@router.get("/buscar", response_model=RespuestaSugerencias)
def busqueda_semantica(
    db: DbSession,
    q: str = Query(min_length=3, description="Pregunta o descripción en lenguaje natural"),
    en: Literal["oportunidades", "proyectos"] = "oportunidades",
    limite: int = Query(default=8, le=30),
):
    """Busca por significado y no solo por palabras exactas: «plata para un piloto de agua» encuentra fondos de acueductos."""
    if en == "oportunidades":
        candidatos = _abiertas(db)
        resultados, metodo = ordenar(db, q, "oportunidad", candidatos, textos.oportunidad, limite)
        items = [Sugerencia(id=r.objeto.id, tipo="oportunidad", titulo=r.objeto.titulo,
                            detalle=f"{r.objeto.entidad} · cierra el {r.objeto.cierra_en.isoformat()}",
                            similitud=r.similitud, razon=f"Relevancia {_pct(r)}") for r in resultados]
    else:
        candidatos = list(db.scalars(select(Proyecto)).unique())
        resultados, metodo = ordenar(db, q, "proyecto", candidatos, textos.proyecto, limite)
        items = [Sugerencia(id=r.objeto.id, tipo="proyecto", titulo=r.objeto.titulo,
                            detalle=f"{r.objeto.area.nombre} · {r.objeto.lider}",
                            similitud=r.similitud, razon=f"Relevancia {_pct(r)}") for r in resultados]
    return RespuestaSugerencias(metodo=metodo, resultados=items)


@router.get("/para-mi", response_model=SugerenciasParaMi)
def sugerencias_para_mi(usuario: UsuarioActual, db: DbSession):
    """Sugerencias del perfil: proyectos donde encajo y oportunidades para mis proyectos."""
    mios_ids = set(db.scalars(select(Miembro.proyecto_id).where(Miembro.usuario_id == usuario.id)))
    mis_proyectos = list(db.scalars(
        select(Proyecto).where(or_(Proyecto.creado_por_id == usuario.id, Proyecto.id.in_(mios_ids)))).unique())
    mios_ids |= {p.id for p in mis_proyectos}

    perfil = textos.usuario(usuario)
    proyectos: list[Sugerencia] = []
    metodo = "lexico" if codificador.obtener() is None else "semantico"
    if perfil:
        abiertos = [p for p in db.scalars(select(Proyecto)).unique()
                    if p.id not in mios_ids and p.estado.value not in ("finalizado", "pausado")]
        resultados, metodo = ordenar(db, perfil, "proyecto", abiertos, textos.proyecto, limite=5)
        for r in resultados:
            p: Proyecto = r.objeto
            comunes = _comunes(textos.proyecto(p), ", ".join(usuario.habilidades + usuario.intereses))
            proyectos.append(Sugerencia(
                id=p.id, tipo="proyecto", titulo=p.titulo, detalle=f"{p.area.nombre} · {p.lider}", similitud=r.similitud,
                razon=f"Encaja con tu perfil en un {_pct(r)}" + (f": {', '.join(comunes)}." if comunes else "."),
            ))

    oportunidades: dict[uuid.UUID, Sugerencia] = {}
    abiertas = _abiertas(db)
    for p in mis_proyectos:
        for rec in puntuar(p, abiertas, limite=2, semantica=_semantica(db, p, abiertas)):
            if rec.oportunidad_id not in oportunidades or oportunidades[rec.oportunidad_id].similitud < rec.puntaje:
                oportunidades[rec.oportunidad_id] = Sugerencia(
                    id=rec.oportunidad_id, tipo="oportunidad", titulo=rec.titulo, detalle=f"Para «{p.titulo}»",
                    similitud=rec.puntaje, razon=rec.razon,
                )

    return SugerenciasParaMi(
        metodo=metodo,
        perfil_completo=bool(usuario.habilidades and usuario.intereses),
        proyectos=proyectos,
        oportunidades=sorted(oportunidades.values(), key=lambda s: s.similitud, reverse=True)[:6],
    )
