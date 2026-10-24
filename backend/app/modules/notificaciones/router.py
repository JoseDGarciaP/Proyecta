import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select, update

from app.core.deps import DbSession, UsuarioActual
from app.modules.notificaciones.models import Notificacion
from app.modules.notificaciones.schemas import Conteo, NotificacionSalida, PreferenciasCorreo
from app.modules.usuarios.models import AVISOS_POR_DEFECTO

router = APIRouter(prefix="/api/notificaciones", tags=["notificaciones"])


@router.get("", response_model=list[NotificacionSalida])
def listar(usuario: UsuarioActual, db: DbSession, solo_no_leidas: bool = False,
           limite: int = Query(default=30, ge=1, le=100), offset: int = 0):
    stmt = select(Notificacion).where(Notificacion.usuario_id == usuario.id)
    if solo_no_leidas:
        stmt = stmt.where(Notificacion.leida.is_(False))
    return db.scalars(stmt.order_by(Notificacion.creada_en.desc()).limit(limite).offset(offset)).all()


@router.get("/conteo", response_model=Conteo)
def conteo(usuario: UsuarioActual, db: DbSession):
    n = db.scalar(select(func.count()).where(Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False)))
    return Conteo(no_leidas=n or 0)


@router.post("/{notificacion_id}/leida", response_model=NotificacionSalida)
def marcar_leida(notificacion_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    aviso = db.get(Notificacion, notificacion_id)
    if aviso is None or aviso.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    aviso.leida = True
    db.commit()
    return aviso


@router.post("/leidas", status_code=status.HTTP_204_NO_CONTENT)
def marcar_todas(usuario: UsuarioActual, db: DbSession):
    db.execute(update(Notificacion).where(Notificacion.usuario_id == usuario.id, Notificacion.leida.is_(False)).values(leida=True))
    db.commit()


@router.delete("/{notificacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(notificacion_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    aviso = db.get(Notificacion, notificacion_id)
    if aviso is None or aviso.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    db.delete(aviso)
    db.commit()


@router.get("/preferencias", response_model=PreferenciasCorreo)
def leer_preferencias(usuario: UsuarioActual):
    return PreferenciasCorreo(**{**AVISOS_POR_DEFECTO, **(usuario.correo_avisos or {})})


@router.put("/preferencias", response_model=PreferenciasCorreo)
def guardar_preferencias(datos: PreferenciasCorreo, usuario: UsuarioActual, db: DbSession):
    usuario.correo_avisos = datos.model_dump()
    db.commit()
    return datos
