"""Registro de aportes de cada miembro y su validación por el responsable (Ep6-Hu11)."""

import uuid
from datetime import date, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.database import utcnow
from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.router import es_miembro
from app.modules.aportes.models import Aporte, EstadoAporte
from app.modules.notificaciones.models import TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.proyectos.router import obtener_proyecto
from app.modules.roles.servicio import puede

router = APIRouter(tags=["aportes"])


class AporteEntrada(BaseModel):
    tipo: str = Field(min_length=2, max_length=120)
    descripcion: str = Field(min_length=5, max_length=2000)
    horas: int | None = Field(default=None, ge=0, le=10000)
    valor: int | None = Field(default=None, ge=0)
    fecha: date


class Revision(BaseModel):
    comentario: str = Field(default="", max_length=1000)


class AporteSalida(BaseModel):
    id: uuid.UUID
    proyecto_id: uuid.UUID
    usuario_id: uuid.UUID | None
    usuario: str
    tipo: str
    descripcion: str
    horas: int | None
    valor: int | None
    fecha: date
    estado: EstadoAporte
    comentario: str
    validado_en: datetime | None
    creado_en: datetime


class ResumenAportes(BaseModel):
    aportes: list[AporteSalida]
    horas_validadas: int
    valor_validado: int


def _salida(a: Aporte) -> AporteSalida:
    return AporteSalida(id=a.id, proyecto_id=a.proyecto_id, usuario_id=a.usuario_id,
                        usuario=a.usuario.nombre if a.usuario else "Usuario eliminado", tipo=a.tipo, descripcion=a.descripcion,
                        horas=a.horas, valor=a.valor, fecha=a.fecha, estado=a.estado, comentario=a.comentario,
                        validado_en=a.validado_en, creado_en=a.creado_en)


@router.get("/api/proyectos/{proyecto_id}/aportes", response_model=ResumenAportes)
def listar(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """El equipo ve todos; el resto solo los validados."""
    proyecto = obtener_proyecto(db, proyecto_id)
    stmt = select(Aporte).where(Aporte.proyecto_id == proyecto.id).order_by(Aporte.fecha.desc(), Aporte.creado_en.desc())
    if not es_miembro(db, proyecto, usuario.id) and not puede(db, usuario, "proyectos.moderar"):
        stmt = stmt.where(Aporte.estado == EstadoAporte.VALIDADO)
    aportes = list(db.scalars(stmt))
    validados = [a for a in aportes if a.estado == EstadoAporte.VALIDADO]
    return ResumenAportes(aportes=[_salida(a) for a in aportes], horas_validadas=sum(a.horas or 0 for a in validados),
                          valor_validado=sum(a.valor or 0 for a in validados))


@router.post("/api/proyectos/{proyecto_id}/aportes", response_model=AporteSalida, status_code=status.HTTP_201_CREATED)
def registrar_aporte(proyecto_id: uuid.UUID, datos: AporteEntrada, usuario: UsuarioActual, db: DbSession,
                     tareas: BackgroundTasks):
    proyecto = obtener_proyecto(db, proyecto_id)
    if not es_miembro(db, proyecto, usuario.id):
        raise HTTPException(status_code=403, detail="Solo el equipo del proyecto puede registrar aportes")
    if datos.fecha > date.today():
        raise HTTPException(status_code=422, detail="La fecha del aporte no puede ser futura")
    es_dueno = proyecto.creado_por_id == usuario.id
    a = Aporte(proyecto_id=proyecto.id, usuario_id=usuario.id, tipo=datos.tipo.strip(), descripcion=datos.descripcion.strip(),
               horas=datos.horas, valor=datos.valor, fecha=datos.fecha,
               # Lo que registra el propio responsable no necesita que nadie más lo valide.
               estado=EstadoAporte.VALIDADO if es_dueno else EstadoAporte.PENDIENTE,
               validado_por_id=usuario.id if es_dueno else None, validado_en=utcnow() if es_dueno else None)
    db.add(a)
    if not es_dueno and proyecto.creado_por is not None:
        notificar(db, proyecto.creado_por, TipoNotificacion.PROYECTO, f"{usuario.nombre} registró un aporte en «{proyecto.titulo}»",
                  f"{a.tipo}: {a.descripcion[:140]}. Revísalo para validarlo.", f"/proyectos/{proyecto.id}", tareas)
    db.commit()
    return _salida(a)


def _revisar(aporte_id: uuid.UUID, datos: Revision, usuario, db, tareas, estado: EstadoAporte) -> AporteSalida:
    a = db.get(Aporte, aporte_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Aporte no encontrado")
    proyecto = obtener_proyecto(db, a.proyecto_id)
    if usuario.id != proyecto.creado_por_id and not puede(db, usuario, "proyectos.moderar"):
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto valida los aportes")
    if a.estado != EstadoAporte.PENDIENTE:
        raise HTTPException(status_code=409, detail=f"El aporte ya fue {a.estado.value}")
    if estado == EstadoAporte.RECHAZADO and len(datos.comentario.strip()) < 5:
        raise HTTPException(status_code=422, detail="Explica por qué no se valida el aporte")
    a.estado, a.comentario, a.validado_por_id, a.validado_en = estado, datos.comentario.strip(), usuario.id, utcnow()
    if a.usuario is not None:
        notificar(db, a.usuario, TipoNotificacion.PROYECTO, f"Tu aporte en «{proyecto.titulo}» fue {estado.value}",
                  a.comentario or a.descripcion[:140], f"/proyectos/{proyecto.id}", tareas)
    db.commit()
    return _salida(a)


@router.post("/api/aportes/{aporte_id}/validar", response_model=AporteSalida)
def validar(aporte_id: uuid.UUID, datos: Revision, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    return _revisar(aporte_id, datos, usuario, db, tareas, EstadoAporte.VALIDADO)


@router.post("/api/aportes/{aporte_id}/rechazar", response_model=AporteSalida)
def rechazar(aporte_id: uuid.UUID, datos: Revision, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    return _revisar(aporte_id, datos, usuario, db, tareas, EstadoAporte.RECHAZADO)


@router.delete("/api/aportes/{aporte_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar(aporte_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    a = db.get(Aporte, aporte_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Aporte no encontrado")
    if a.usuario_id != usuario.id or a.estado != EstadoAporte.PENDIENTE:
        raise HTTPException(status_code=403, detail="Solo puedes borrar tus aportes que aún no se han revisado")
    db.delete(a)
    db.commit()
