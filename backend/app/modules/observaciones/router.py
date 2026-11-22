"""Observaciones y aportes en la ficha de un proyecto (Ep4-Hu23) y su moderación (Ep4-Hu27)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.database import utcnow
from app.core.deps import Admin, DbSession, UsuarioActual, requiere
from app.modules.admin.bitacora import registrar
from app.modules.notificaciones.models import TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.observaciones.models import Observacion
from app.modules.proyectos.router import obtener_proyecto
from app.modules.roles.servicio import puede

router = APIRouter(tags=["observaciones"])
admin = APIRouter(prefix="/api/admin/observaciones", tags=["administración"], dependencies=[Depends(requiere("admin.moderacion"))])


class ObservacionEntrada(BaseModel):
    texto: str = Field(min_length=2, max_length=3000)


class Motivo(BaseModel):
    motivo: str = Field(min_length=5, max_length=1000)


class ObservacionSalida(BaseModel):
    id: uuid.UUID
    proyecto_id: uuid.UUID
    autor_id: uuid.UUID | None
    autor: str
    texto: str
    oculta: bool
    motivo_oculta: str
    creado_en: datetime
    editado_en: datetime | None


def _salida(o: Observacion) -> ObservacionSalida:
    return ObservacionSalida(id=o.id, proyecto_id=o.proyecto_id, autor_id=o.autor_id,
                             autor=o.autor.nombre if o.autor else "Usuario eliminado", texto=o.texto, oculta=o.oculta,
                             motivo_oculta=o.motivo_oculta, creado_en=o.creado_en, editado_en=o.editado_en)


def _obtener(db, observacion_id: uuid.UUID) -> Observacion:
    o = db.get(Observacion, observacion_id)
    if o is None:
        raise HTTPException(status_code=404, detail="Observación no encontrada")
    return o


@router.get("/api/proyectos/{proyecto_id}/observaciones", response_model=list[ObservacionSalida])
def listar(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """Las ocultas solo las ven su autor y quien modera."""
    obtener_proyecto(db, proyecto_id)
    moderador = puede(db, usuario, "admin.moderacion")
    filas = db.scalars(select(Observacion).where(Observacion.proyecto_id == proyecto_id).order_by(Observacion.creado_en))
    return [_salida(o) for o in filas if not o.oculta or moderador or o.autor_id == usuario.id]


@router.post("/api/proyectos/{proyecto_id}/observaciones", response_model=ObservacionSalida, status_code=status.HTTP_201_CREATED)
def crear(proyecto_id: uuid.UUID, datos: ObservacionEntrada, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    proyecto = obtener_proyecto(db, proyecto_id)
    if proyecto.archivado:
        raise HTTPException(status_code=409, detail="El proyecto está archivado")
    o = Observacion(proyecto_id=proyecto.id, autor_id=usuario.id, texto=datos.texto.strip())
    db.add(o)
    dueno = proyecto.creado_por
    if dueno is not None and dueno.id != usuario.id:
        notificar(db, dueno, TipoNotificacion.OBSERVACION, f"Nueva observación en «{proyecto.titulo}»",
                  f"{usuario.nombre}: {o.texto[:160]}", f"/proyectos/{proyecto.id}#observaciones", tareas,
                  parrafos=[f"{usuario.nombre} dejó una observación:", o.texto[:1000]])
    db.commit()
    return _salida(o)


@router.patch("/api/observaciones/{observacion_id}", response_model=ObservacionSalida)
def editar(observacion_id: uuid.UUID, datos: ObservacionEntrada, usuario: UsuarioActual, db: DbSession):
    o = _obtener(db, observacion_id)
    if o.autor_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo quien escribió la observación puede editarla")
    o.texto, o.editado_en = datos.texto.strip(), utcnow()
    db.commit()
    return _salida(o)


@router.delete("/api/observaciones/{observacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(observacion_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    o = _obtener(db, observacion_id)
    if o.autor_id != usuario.id and not puede(db, usuario, "admin.moderacion"):
        raise HTTPException(status_code=403, detail="Solo quien escribió la observación puede borrarla")
    db.delete(o)
    db.commit()


@admin.post("/{observacion_id}/ocultar", response_model=ObservacionSalida)
def ocultar(observacion_id: uuid.UUID, datos: Motivo, quien: Admin, db: DbSession, tareas: BackgroundTasks):
    o = _obtener(db, observacion_id)
    o.oculta, o.motivo_oculta = True, datos.motivo.strip()
    if o.autor is not None:
        notificar(db, o.autor, TipoNotificacion.MODERACION, "Se ocultó una observación tuya", f"Motivo: {o.motivo_oculta}",
                  f"/proyectos/{o.proyecto_id}#observaciones", tareas, detalles=[("Motivo", o.motivo_oculta)])
    registrar(db, quien, "observacion.ocultar", o.texto[:120], f"Motivo: {o.motivo_oculta}")
    db.commit()
    return _salida(o)


@admin.post("/{observacion_id}/restaurar", response_model=ObservacionSalida)
def restaurar(observacion_id: uuid.UUID, quien: Admin, db: DbSession):
    o = _obtener(db, observacion_id)
    o.oculta, o.motivo_oculta = False, ""
    registrar(db, quien, "observacion.restaurar", o.texto[:120])
    db.commit()
    return _salida(o)
