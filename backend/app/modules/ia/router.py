import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select

from app.core.config import get_settings
from app.core.database import utcnow
from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.models import Miembro
from app.modules.ia import historial
from app.modules.ia.models import EstadoRecomendacion, RecomendacionGuardada, TipoRecomendacion, ValoracionDiagnostico
from app.modules.ia.schemas import (
    Anular,
    RecomendacionSalida,
    ResumenValoraciones,
    Valoracion,
    RespuestaAnalisis,
    RespuestaPitch,
    RespuestaSugerencias,
    Sugerencia,
    SugerenciasParaMi,
)
from app.modules.ia.servicio import analizar, generar_pitch, puntuar
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.router import obtener_proyecto
from app.modules.similitud import codificador, textos
from app.modules.similitud.servicio import MINIMO, Resultado, ordenar, similitudes
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/ia", tags=["inteligencia artificial"])


@router.get("/estado")
def estado():
    settings = get_settings()
    modelo = {
        "ollama": settings.ollama_model,
        "groq": settings.groq_model,
        "anthropic": settings.anthropic_model,
    }.get(settings.ia_proveedor)
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


def _anuladas(db, proyecto_id: uuid.UUID, tipo: TipoRecomendacion) -> set[uuid.UUID]:
    """Lo que el equipo descartó: no se vuelve a sugerir (Ep5-Hu6)."""
    return set(db.scalars(select(RecomendacionGuardada.objetivo_id).where(
        RecomendacionGuardada.proyecto_id == proyecto_id, RecomendacionGuardada.tipo == tipo,
        RecomendacionGuardada.estado == EstadoRecomendacion.ANULADA)))


@router.post("/proyectos/{proyecto_id}/analisis", response_model=RespuestaAnalisis)
async def analizar_proyecto(proyecto_id: uuid.UUID, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    descartadas = _anuladas(db, proyecto.id, TipoRecomendacion.OPORTUNIDAD)
    oportunidades = [o for o in _abiertas(db) if o.id not in descartadas]
    semantica = _semantica(db, proyecto, oportunidades)
    respuesta = await analizar(proyecto, oportunidades, semantica)
    # Ep5-Hu9: se citan los proyectos parecidos en que se apoyan las mejoras.
    respuesta.similares = proyectos_similares(proyecto_id, db, limite=3).resultados
    # HU-05: las recomendaciones quedan guardadas con fecha y estado «pendiente».
    guardadas = historial.guardar(db, proyecto.id, TipoRecomendacion.OPORTUNIDAD, [
        historial.Item(r.oportunidad_id, r.titulo, r.puntaje, r.razon) for r in respuesta.recomendaciones
    ])
    for r in respuesta.recomendaciones:
        g = guardadas[r.oportunidad_id]
        r.recomendacion_id, r.estado, r.fecha = g.id, g.estado.value, g.creado_en
    return respuesta


@router.get("/proyectos/{proyecto_id}/recomendaciones", response_model=list[RecomendacionSalida])
def recomendaciones_guardadas(
    proyecto_id: uuid.UUID,
    db: DbSession,
    tipo: TipoRecomendacion | None = None,
    estado: EstadoRecomendacion | None = None,
):
    """Historial de recomendaciones del proyecto (convocatorias y colaboradores), de la más reciente a la más antigua."""
    obtener_proyecto(db, proyecto_id)
    stmt = select(RecomendacionGuardada).where(RecomendacionGuardada.proyecto_id == proyecto_id)
    if tipo:
        stmt = stmt.where(RecomendacionGuardada.tipo == tipo)
    if estado:
        stmt = stmt.where(RecomendacionGuardada.estado == estado)
    return [
        RecomendacionSalida(
            id=r.id, proyecto_id=r.proyecto_id, tipo=r.tipo.value, objetivo_id=r.objetivo_id, titulo=r.titulo,
            puntaje=r.puntaje, razon=r.razon, estado=r.estado.value, creado_en=r.creado_en,
            motivo=r.motivo or "", decidido_en=r.decidido_en,
        )
        for r in db.scalars(stmt.order_by(RecomendacionGuardada.creado_en.desc()))
    ]


def _decidir(db, recomendacion_id: uuid.UUID, usuario: Usuario, estado: EstadoRecomendacion, motivo: str = ""):
    from app.modules.admin.bitacora import registrar
    from app.modules.alianzas.router import es_miembro

    r = db.get(RecomendacionGuardada, recomendacion_id)
    if r is None:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    proyecto = obtener_proyecto(db, r.proyecto_id)
    if not es_miembro(db, proyecto, usuario.id):
        raise HTTPException(status_code=403, detail="Solo el equipo del proyecto puede decidir sobre sus recomendaciones")
    if r.estado != EstadoRecomendacion.PENDIENTE:
        raise HTTPException(status_code=409, detail=f"La recomendación ya fue {r.estado.value}")
    r.estado, r.motivo, r.decidido_por_id, r.decidido_en = estado, motivo, usuario.id, utcnow()
    registrar(db, usuario, f"recomendacion.{'aceptar' if estado == EstadoRecomendacion.ACEPTADA else 'anular'}",
              r.titulo, f"Proyecto «{proyecto.titulo}»" + (f". Motivo: {motivo}" if motivo else ""))
    db.commit()
    return RecomendacionSalida(
        id=r.id, proyecto_id=r.proyecto_id, tipo=r.tipo.value, objetivo_id=r.objetivo_id, titulo=r.titulo,
        puntaje=r.puntaje, razon=r.razon, estado=r.estado.value, creado_en=r.creado_en, motivo=r.motivo, decidido_en=r.decidido_en,
    )


@router.post("/recomendaciones/{recomendacion_id}/aceptar", response_model=RecomendacionSalida)
def aceptar_recomendacion(recomendacion_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """El equipo toma la recomendación (Ep5-Hu5)."""
    return _decidir(db, recomendacion_id, usuario, EstadoRecomendacion.ACEPTADA)


@router.post("/recomendaciones/{recomendacion_id}/anular", response_model=RecomendacionSalida)
def anular_recomendacion(recomendacion_id: uuid.UUID, datos: Anular, usuario: UsuarioActual, db: DbSession):
    """El equipo la descarta con un motivo y no se vuelve a sugerir (Ep5-Hu6)."""
    return _decidir(db, recomendacion_id, usuario, EstadoRecomendacion.ANULADA, datos.motivo.strip())


def _resumen_valoraciones(db, proyecto_id: uuid.UUID, usuario: Usuario) -> ResumenValoraciones:
    valoraciones = list(db.scalars(select(ValoracionDiagnostico).where(ValoracionDiagnostico.proyecto_id == proyecto_id)))
    mia = next((v.util for v in valoraciones if v.usuario_id == usuario.id), None)
    return ResumenValoraciones(utiles=sum(v.util for v in valoraciones), no_utiles=sum(not v.util for v in valoraciones), mia=mia)


@router.get("/proyectos/{proyecto_id}/diagnostico/valoracion", response_model=ResumenValoraciones)
def ver_valoraciones(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    obtener_proyecto(db, proyecto_id)
    return _resumen_valoraciones(db, proyecto_id, usuario)


@router.post("/proyectos/{proyecto_id}/diagnostico/valoracion", response_model=ResumenValoraciones,
             status_code=status.HTTP_201_CREATED)
def valorar_diagnostico(proyecto_id: uuid.UUID, datos: Valoracion, usuario: UsuarioActual, db: DbSession):
    """Marca las mejoras sugeridas como útiles o no (Ep5-Hu9). Una valoración por persona; se puede cambiar."""
    obtener_proyecto(db, proyecto_id)
    v = db.scalar(select(ValoracionDiagnostico).where(ValoracionDiagnostico.proyecto_id == proyecto_id,
                                                      ValoracionDiagnostico.usuario_id == usuario.id))
    if v is None:
        v = ValoracionDiagnostico(proyecto_id=proyecto_id, usuario_id=usuario.id, util=datos.util)
        db.add(v)
    v.util, v.comentario = datos.util, datos.comentario.strip()
    db.commit()
    return _resumen_valoraciones(db, proyecto_id, usuario)


@router.post("/proyectos/{proyecto_id}/pitch/{oportunidad_id}", response_model=RespuestaPitch)
async def redactar_pitch_postulacion(proyecto_id: uuid.UUID, oportunidad_id: uuid.UUID, db: DbSession):
    """Redacta un borrador de carta de postulación cruzando la ficha del proyecto con la oportunidad."""
    proyecto = obtener_proyecto(db, proyecto_id)
    oportunidad = db.get(Oportunidad, oportunidad_id)
    if oportunidad is None:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return await generar_pitch(proyecto, oportunidad)


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


# Peso de la coincidencia directa de habilidades frente a la similitud del perfil completo.
PESO_HABILIDADES = 0.3
# Con este número de habilidades requeridas en común el factor llega a su máximo.
HABILIDADES_PARA_MAXIMO = 3


def _factor_habilidades(u: Usuario, proyecto: Proyecto) -> tuple[float, list[str]]:
    """Habilidades del usuario que el proyecto pide en sus necesidades o etiquetas, y un factor de 0 a 1.

    Compara palabra a palabra sin tildes ni plurales: «Python» coincide con «programación en Python».
    """
    requeridas = textos.palabras(" ".join([proyecto.necesidades, *proyecto.etiquetas]))
    coinciden = [h for h in dict.fromkeys(set(u.habilidades)) if h and textos.palabras(h) & requeridas]
    coinciden.sort(key=str.lower)
    return min(1.0, len(coinciden) / HABILIDADES_PARA_MAXIMO), coinciden


@router.get("/proyectos/{proyecto_id}/colaboradores", response_model=RespuestaSugerencias)
def colaboradores_sugeridos(proyecto_id: uuid.UUID, db: DbSession, _: UsuarioActual, limite: int = Query(default=5, le=20),
                            peso_habilidades: float = Query(default=PESO_HABILIDADES, ge=0, le=1)):
    """Personas cuyo perfil (habilidades, intereses, programa) encaja con lo que el proyecto necesita.

    Solo cuentas activas que no son de administración ni ya están en el equipo. El puntaje combina la
    similitud del perfil completo (70 %) con las habilidades que el proyecto pide de forma directa (30 %).
    Quien consulta puede mover ese peso con `peso_habilidades` (Ep5-Hu4). Las personas descartadas no vuelven.
    """
    proyecto = obtener_proyecto(db, proyecto_id)
    ya = {m for m in db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id))}
    ya.add(proyecto.creado_por_id)
    ya |= _anuladas(db, proyecto.id, TipoRecomendacion.COLABORADOR)
    candidatos = [u for u in db.scalars(select(Usuario).where(Usuario.activo.is_(True), Usuario.rol != Rol.ADMIN.value))
                  if u.id not in ya and textos.usuario(u)]
    consulta = textos.necesidades(proyecto)
    sims, metodo = similitudes(db, consulta, "usuario", candidatos, textos.usuario)
    puntuados = []
    for u in candidatos:
        similitud = sims.get(u.id, 0.0)
        factor, habilidades = _factor_habilidades(u, proyecto)
        if similitud < MINIMO[metodo] and not habilidades:
            continue
        puntaje = round((1 - peso_habilidades) * similitud + peso_habilidades * factor, 3)
        puntuados.append((puntaje, u, habilidades))
    puntuados.sort(key=lambda x: x[0], reverse=True)

    salida = []
    for puntaje, u, habilidades in puntuados[:limite]:
        if habilidades:
            razon = f"Tiene {len(habilidades)} habilidad(es) que el proyecto requiere: {', '.join(habilidades)}."
        else:
            comunes = _comunes(consulta, ", ".join(u.habilidades + u.intereses))
            razon = f"Su perfil coincide en un {round(puntaje * 100)} % con lo que busca el proyecto" + (
                f": {', '.join(comunes)}." if comunes else ".")
        salida.append(Sugerencia(
            id=u.id, tipo="usuario", titulo=u.nombre, detalle=u.programa or u.rol_nombre, similitud=puntaje, razon=razon,
        ))
    # HU-05: los colaboradores sugeridos también quedan guardados con fecha y estado «pendiente».
    guardadas = historial.guardar(db, proyecto.id, TipoRecomendacion.COLABORADOR, [
        historial.Item(s.id, s.titulo, s.similitud, s.razon) for s in salida
    ])
    for s in salida:
        g = guardadas[s.id]
        s.recomendacion_id, s.estado, s.fecha = g.id, g.estado.value, g.creado_en
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
