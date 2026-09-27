import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.models import EstadoSolicitud, Miembro, Solicitud, TipoSolicitud
from app.modules.alianzas.schemas import (
    MiembroSalida, NuevaInvitacion, NuevaSolicitud, Respuesta, SolicitudSalida, responde,
)
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.router import obtener_proyecto
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(tags=["alianzas"])


def es_miembro(db: Session, proyecto: Proyecto, usuario_id: uuid.UUID) -> bool:
    return proyecto.creado_por_id == usuario_id or db.get(Miembro, (proyecto.id, usuario_id)) is not None


def _validar_nueva(db: Session, proyecto: Proyecto, usuario_id: uuid.UUID) -> None:
    if es_miembro(db, proyecto, usuario_id):
        raise HTTPException(status_code=409, detail="Esa persona ya hace parte del proyecto")
    pendiente = db.scalar(select(Solicitud.id).where(
        Solicitud.proyecto_id == proyecto.id, Solicitud.usuario_id == usuario_id,
        Solicitud.estado == EstadoSolicitud.PENDIENTE,
    ))
    if pendiente:
        raise HTTPException(status_code=409, detail="Ya hay una solicitud pendiente para este proyecto")


@router.post("/api/proyectos/{proyecto_id}/solicitudes", response_model=SolicitudSalida, status_code=status.HTTP_201_CREATED)
def solicitar_union(proyecto_id: uuid.UUID, datos: NuevaSolicitud, usuario: UsuarioActual, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    if proyecto.creado_por_id is None:
        raise HTTPException(status_code=409, detail="El proyecto no tiene un responsable que pueda responder")
    _validar_nueva(db, proyecto, usuario.id)
    solicitud = Solicitud(proyecto=proyecto, usuario=usuario, tipo=TipoSolicitud.SOLICITUD, mensaje=datos.mensaje.strip())
    db.add(solicitud)
    db.commit()
    return SolicitudSalida.de(solicitud, usuario.id)


@router.post("/api/proyectos/{proyecto_id}/invitaciones", response_model=SolicitudSalida, status_code=status.HTTP_201_CREATED)
def invitar(proyecto_id: uuid.UUID, datos: NuevaInvitacion, usuario: UsuarioActual, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    if proyecto.creado_por_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto puede invitar")
    invitado = db.get(Usuario, datos.usuario_id)
    if invitado is None or not invitado.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    _validar_nueva(db, proyecto, invitado.id)
    solicitud = Solicitud(proyecto=proyecto, usuario=invitado, tipo=TipoSolicitud.INVITACION, mensaje=datos.mensaje.strip())
    db.add(solicitud)
    db.commit()
    return SolicitudSalida.de(solicitud, usuario.id)


@router.get("/api/proyectos/{proyecto_id}/miembros", response_model=list[MiembroSalida])
def listar_miembros(proyecto_id: uuid.UUID, db: DbSession):
    obtener_proyecto(db, proyecto_id)
    miembros = db.scalars(select(Miembro).where(Miembro.proyecto_id == proyecto_id).order_by(Miembro.desde))
    return [MiembroSalida.de(m) for m in miembros]


@router.delete("/api/proyectos/{proyecto_id}/miembros/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def retirar_miembro(proyecto_id: uuid.UUID, usuario_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """Quien registró el proyecto (o un admin) retira a alguien; un miembro puede retirarse a sí mismo."""
    proyecto = obtener_proyecto(db, proyecto_id)
    if usuario.id not in (usuario_id, proyecto.creado_por_id) and usuario.rol != Rol.ADMIN:
        raise HTTPException(status_code=403, detail="No puedes retirar a este miembro")
    miembro = db.get(Miembro, (proyecto_id, usuario_id))
    if miembro is None:
        raise HTTPException(status_code=404, detail="No es miembro del proyecto")
    db.delete(miembro)
    db.commit()


def solicitudes_de(db: Session, usuario_id: uuid.UUID) -> list[Solicitud]:
    """Las que envié, las que me enviaron y las de los proyectos que registré."""
    stmt = (
        select(Solicitud).join(Solicitud.proyecto)
        .where(or_(Solicitud.usuario_id == usuario_id, Proyecto.creado_por_id == usuario_id))
        .order_by(Solicitud.creado_en.desc(), Solicitud.actualizado_en.desc())
    )
    return list(db.scalars(stmt).unique())


@router.get("/api/alianzas", response_model=list[SolicitudSalida])
def mis_solicitudes(usuario: UsuarioActual, db: DbSession, estado: EstadoSolicitud | None = None):
    return [SolicitudSalida.de(s, usuario.id) for s in solicitudes_de(db, usuario.id) if estado in (None, s.estado)]


def _obtener(db: Session, solicitud_id: uuid.UUID) -> Solicitud:
    solicitud = db.get(Solicitud, solicitud_id)
    if solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise HTTPException(status_code=409, detail=f"La solicitud ya fue {solicitud.estado.value}")
    return solicitud


def _cerrar(db: Session, solicitud: Solicitud, estado: EstadoSolicitud, respuesta: str, yo: uuid.UUID) -> SolicitudSalida:
    solicitud.estado = estado
    solicitud.respuesta = respuesta.strip()
    solicitud.respondida_en = utcnow()
    if estado == EstadoSolicitud.ACEPTADA and db.get(Miembro, (solicitud.proyecto_id, solicitud.usuario_id)) is None:
        db.add(Miembro(proyecto_id=solicitud.proyecto_id, usuario_id=solicitud.usuario_id))
    db.commit()
    return SolicitudSalida.de(solicitud, yo)


def _decidir(solicitud_id: uuid.UUID, datos: Respuesta, usuario: Usuario, db: Session, estado: EstadoSolicitud):
    solicitud = _obtener(db, solicitud_id)
    if responde(solicitud) != usuario.id:
        raise HTTPException(status_code=403, detail="Esta solicitud la responde otra persona")
    return _cerrar(db, solicitud, estado, datos.respuesta, usuario.id)


@router.post("/api/alianzas/{solicitud_id}/aceptar", response_model=SolicitudSalida)
def aceptar(solicitud_id: uuid.UUID, datos: Respuesta, usuario: UsuarioActual, db: DbSession):
    return _decidir(solicitud_id, datos, usuario, db, EstadoSolicitud.ACEPTADA)


@router.post("/api/alianzas/{solicitud_id}/rechazar", response_model=SolicitudSalida)
def rechazar(solicitud_id: uuid.UUID, datos: Respuesta, usuario: UsuarioActual, db: DbSession):
    return _decidir(solicitud_id, datos, usuario, db, EstadoSolicitud.RECHAZADA)


@router.post("/api/alianzas/{solicitud_id}/cancelar", response_model=SolicitudSalida)
def cancelar(solicitud_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """Quien envió la solicitud o la invitación la retira antes de que respondan."""
    solicitud = _obtener(db, solicitud_id)
    if responde(solicitud) == usuario.id or usuario.id not in (solicitud.usuario_id, solicitud.proyecto.creado_por_id):
        raise HTTPException(status_code=403, detail="Solo quien la envió puede cancelarla")
    return _cerrar(db, solicitud, EstadoSolicitud.CANCELADA, "", usuario.id)
