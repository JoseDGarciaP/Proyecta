import uuid
from datetime import date
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.core.deps import Admin, DbSession, UsuarioActual, requiere
from app.modules.admin.bitacora import registrar
from app.modules.alianzas.models import Miembro
from app.modules.alianzas.router import es_miembro
from app.modules.experiencia.servicio import sumar, sumar_a_varios
from app.modules.notificaciones.models import TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.oportunidades.models import Oportunidad
from app.modules.postulaciones.models import EstadoPostulacion, Postulacion
from app.modules.proyectos.models import Proyecto
from app.modules.roles.servicio import puede, usuarios_con_permiso
from app.modules.usuarios.models import Usuario

router = APIRouter(tags=["postulaciones"])
admin = APIRouter(prefix="/api/admin/postulaciones", tags=["administración"],
                  dependencies=[Depends(requiere("oportunidades.gestionar"))])

ESTADO_TEXTO = {"enviada": "enviada", "aceptada": "seleccionada", "no_seleccionada": "no seleccionada", "retirada": "retirada"}


class NuevaPostulacion(BaseModel):
    proyecto_id: uuid.UUID
    nota: str = Field(min_length=10, max_length=1500, description="Por qué el proyecto encaja con la oportunidad")


class Decision(BaseModel):
    estado: Literal["enviada", "aceptada", "no_seleccionada"]
    comentario: str = Field(default="", max_length=1000)


class PostulacionSalida(BaseModel):
    id: uuid.UUID
    oportunidad_id: uuid.UUID
    oportunidad_titulo: str
    oportunidad_entidad: str
    oportunidad_cierra_en: date
    proyecto_id: uuid.UUID
    proyecto_titulo: str
    usuario_nombre: str | None
    estado: EstadoPostulacion
    nota: str
    comentario: str
    creado_en: str
    decidida_en: str | None

    @classmethod
    def de(cls, p: Postulacion) -> "PostulacionSalida":
        def iso(d):
            return (d if d.tzinfo else d.replace(tzinfo=utcnow().tzinfo)).isoformat() if d else None
        return cls(id=p.id, oportunidad_id=p.oportunidad_id, oportunidad_titulo=p.oportunidad.titulo,
                   oportunidad_entidad=p.oportunidad.entidad, oportunidad_cierra_en=p.oportunidad.cierra_en,
                   proyecto_id=p.proyecto_id, proyecto_titulo=p.proyecto.titulo,
                   usuario_nombre=p.usuario.nombre if p.usuario else None, estado=p.estado, nota=p.nota,
                   comentario=p.comentario, creado_en=iso(p.creado_en), decidida_en=iso(p.decidida_en))


def _equipo(db: Session, proyecto: Proyecto) -> list[uuid.UUID]:
    return [i for i in [proyecto.creado_por_id, *db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id))] if i]


@router.post("/api/oportunidades/{oportunidad_id}/postulaciones", response_model=PostulacionSalida,
             status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere("oportunidades.postular"))])
def postular(oportunidad_id: uuid.UUID, datos: NuevaPostulacion, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    oportunidad = db.get(Oportunidad, oportunidad_id)
    if oportunidad is None:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    if oportunidad.cierra_en < date.today():
        raise HTTPException(status_code=409, detail="La oportunidad ya cerró")
    proyecto = db.get(Proyecto, datos.proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if not es_miembro(db, proyecto, usuario.id):
        raise HTTPException(status_code=403, detail="Solo el equipo del proyecto puede postularlo")
    existente = db.scalar(select(Postulacion).where(Postulacion.oportunidad_id == oportunidad.id, Postulacion.proyecto_id == proyecto.id))
    if existente and existente.estado != EstadoPostulacion.RETIRADA:
        raise HTTPException(status_code=409, detail="Ese proyecto ya está postulado a esta oportunidad")
    postulacion = existente or Postulacion(oportunidad=oportunidad, proyecto=proyecto)
    postulacion.usuario, postulacion.nota, postulacion.estado = usuario, datos.nota.strip(), EstadoPostulacion.ENVIADA
    postulacion.comentario, postulacion.decidida_en, postulacion.creado_en = "", None, utcnow()
    db.add(postulacion)
    db.flush()
    sumar(db, usuario, "postulacion_enviada", f"{oportunidad.id}:{proyecto.id}", f"Postuló «{proyecto.titulo}» a «{oportunidad.titulo}»", tareas)
    # Quien decide las postulaciones las ve en Moderación: se avisa a quien tiene ambos permisos.
    for gestor in usuarios_con_permiso(db, "oportunidades.gestionar"):
        if gestor.id != usuario.id and puede(db, gestor, "admin.moderacion"):
            notificar(db, gestor, TipoNotificacion.REVISION, f"Nueva postulación a «{oportunidad.titulo}»",
                      f"«{proyecto.titulo}» (por {usuario.nombre}): {datos.nota.strip()[:200]}", "/admin/moderacion?seccion=postulaciones", tareas,
                      boton="Revisar postulaciones")
    db.commit()
    return PostulacionSalida.de(postulacion)


@router.get("/api/postulaciones/mias", response_model=list[PostulacionSalida])
def mis_postulaciones(usuario: UsuarioActual, db: DbSession):
    """Postulaciones de los proyectos donde participo."""
    miembro = select(Miembro.proyecto_id).where(Miembro.usuario_id == usuario.id)
    filas = db.scalars(select(Postulacion).join(Proyecto, Proyecto.id == Postulacion.proyecto_id)
                       .where(or_(Proyecto.creado_por_id == usuario.id, Proyecto.id.in_(miembro)))
                       .order_by(Postulacion.creado_en.desc())).unique()
    return [PostulacionSalida.de(p) for p in filas]


@router.get("/api/proyectos/{proyecto_id}/postulaciones", response_model=list[PostulacionSalida])
def postulaciones_proyecto(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """El equipo ve todas; las demás personas solo las seleccionadas."""
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    stmt = select(Postulacion).where(Postulacion.proyecto_id == proyecto_id)
    if not (es_miembro(db, proyecto, usuario.id) or puede(db, usuario, "oportunidades.gestionar")):
        stmt = stmt.where(Postulacion.estado == EstadoPostulacion.ACEPTADA)
    return [PostulacionSalida.de(p) for p in db.scalars(stmt.order_by(Postulacion.creado_en.desc())).unique()]


@router.post("/api/postulaciones/{postulacion_id}/retirar", response_model=PostulacionSalida)
def retirar(postulacion_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    p = db.get(Postulacion, postulacion_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if not es_miembro(db, p.proyecto, usuario.id):
        raise HTTPException(status_code=403, detail="Solo el equipo del proyecto puede retirarla")
    if p.estado != EstadoPostulacion.ENVIADA:
        raise HTTPException(status_code=409, detail=f"La postulación ya fue {ESTADO_TEXTO[p.estado.value]}")
    p.estado, p.decidida_en = EstadoPostulacion.RETIRADA, utcnow()
    db.commit()
    return PostulacionSalida.de(p)


# ---- Gestión (quien administra oportunidades) --------------------------------------------------

@admin.get("", response_model=list[PostulacionSalida])
def listar(db: DbSession, oportunidad_id: uuid.UUID | None = None, estado: EstadoPostulacion | None = None,
           limite: int = Query(default=200, le=500)):
    stmt = select(Postulacion)
    if oportunidad_id:
        stmt = stmt.where(Postulacion.oportunidad_id == oportunidad_id)
    if estado:
        stmt = stmt.where(Postulacion.estado == estado)
    return [PostulacionSalida.de(p) for p in db.scalars(stmt.order_by(Postulacion.creado_en.desc()).limit(limite)).unique()]


@admin.patch("/{postulacion_id}", response_model=PostulacionSalida)
def decidir(postulacion_id: uuid.UUID, datos: Decision, yo: Admin, db: DbSession, tareas: BackgroundTasks):
    p = db.get(Postulacion, postulacion_id)
    if p is None:
        raise HTTPException(status_code=404, detail="Postulación no encontrada")
    if p.estado == EstadoPostulacion.RETIRADA:
        raise HTTPException(status_code=409, detail="El equipo retiró esta postulación")
    if datos.estado == "no_seleccionada" and not datos.comentario.strip():
        raise HTTPException(status_code=422, detail="Explica al equipo por qué no fue seleccionada")
    p.estado, p.comentario = EstadoPostulacion(datos.estado), datos.comentario.strip()
    p.decidida_en = None if p.estado == EstadoPostulacion.ENVIADA else utcnow()
    equipo = _equipo(db, p.proyecto)
    if p.estado == EstadoPostulacion.ACEPTADA:
        sumar_a_varios(db, equipo, "postulacion_aceptada", str(p.id), f"«{p.proyecto.titulo}» seleccionado en «{p.oportunidad.titulo}»", tareas)
    if p.estado != EstadoPostulacion.ENVIADA:
        titulo = (f"¡«{p.proyecto.titulo}» fue seleccionado en «{p.oportunidad.titulo}»!" if p.estado == EstadoPostulacion.ACEPTADA
                  else f"«{p.proyecto.titulo}» no fue seleccionado en «{p.oportunidad.titulo}»")
        for uid in equipo:
            destino = db.get(Usuario, uid)
            if destino:
                notificar(db, destino, TipoNotificacion.POSTULACION, titulo, p.comentario or "", f"/proyectos/{p.proyecto_id}#postulaciones",
                          tareas, detalles=[("Oportunidad", p.oportunidad.titulo), ("Proyecto", p.proyecto.titulo),
                                            ("Estado", ESTADO_TEXTO[p.estado.value])] + ([("Comentario", p.comentario)] if p.comentario else []),
                          boton="Ver el proyecto", parrafos=[])
    registrar(db, yo, "postulacion.decidir", f"{p.proyecto.titulo} → {p.oportunidad.titulo}", ESTADO_TEXTO[p.estado.value])
    if p.estado == EstadoPostulacion.ACEPTADA:
        from app.modules.insignias.servicio import evaluar_ids
        evaluar_ids(db, equipo, tareas)
    db.commit()
    return PostulacionSalida.de(p)
