import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session

from app.core.deps import DbSession, UsuarioActual
from app.modules.actores.models import Actor
from app.modules.catalogo.models import Area, Ods
from app.modules.catalogo.service import area_por_nombre, ods_por_id
from app.modules.proyectos.models import Estado, Proyecto
from app.modules.proyectos.schemas import ProyectoActualizar, ProyectoEntrada, ProyectoSalida
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/proyectos", tags=["proyectos"])


def obtener_proyecto(db: Session, proyecto_id: uuid.UUID) -> Proyecto:
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto


def _verificar_dueno(proyecto: Proyecto, usuario: Usuario) -> None:
    if proyecto.creado_por_id != usuario.id and usuario.rol != Rol.ADMIN:
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto puede modificarlo")


def _actores(db: Session, ids: list[uuid.UUID]) -> list[Actor]:
    items = db.scalars(select(Actor).where(Actor.id.in_(ids))).all() if ids else []
    if len(items) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Algún actor no existe")
    return list(items)


@router.get("", response_model=list[ProyectoSalida])
def listar_proyectos(
    db: DbSession,
    q: str | None = Query(default=None, description="Busca en título, resumen, líder y etiquetas"),
    area: str | None = None,
    estado: Estado | None = None,
    ods: int | None = None,
    limit: int = Query(default=200, le=500),
    offset: int = 0,
):
    stmt = select(Proyecto)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(
            Proyecto.titulo.ilike(patron), Proyecto.resumen.ilike(patron),
            Proyecto.lider.ilike(patron), cast(Proyecto.etiquetas, String).ilike(patron),
        ))
    if area:
        stmt = stmt.join(Proyecto.area).where(Area.nombre == area)
    if estado:
        stmt = stmt.where(Proyecto.estado == estado)
    if ods:
        stmt = stmt.where(Proyecto.ods.any(Ods.id == ods))
    orden = stmt.order_by(Proyecto.creado_en.desc(), Proyecto.actualizado_en.desc()).limit(limit).offset(offset)
    return [ProyectoSalida.de(p) for p in db.scalars(orden).unique()]


@router.post("", response_model=ProyectoSalida, status_code=status.HTTP_201_CREATED)
def crear_proyecto(datos: ProyectoEntrada, usuario: UsuarioActual, db: DbSession):
    proyecto = Proyecto(
        **datos.model_dump(exclude={"area", "ods", "actores", "lider"}),
        lider=datos.lider.strip() or usuario.nombre,
        creado_por_id=usuario.id,
    )
    proyecto.area = area_por_nombre(db, datos.area)
    proyecto.ods = ods_por_id(db, datos.ods)
    proyecto.actores = _actores(db, datos.actores)
    db.add(proyecto)
    db.commit()
    return ProyectoSalida.de(proyecto)


@router.get("/{proyecto_id}", response_model=ProyectoSalida)
def leer_proyecto(proyecto_id: uuid.UUID, db: DbSession):
    return ProyectoSalida.de(obtener_proyecto(db, proyecto_id))


@router.patch("/{proyecto_id}", response_model=ProyectoSalida)
def actualizar_proyecto(proyecto_id: uuid.UUID, datos: ProyectoActualizar, usuario: UsuarioActual, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    _verificar_dueno(proyecto, usuario)
    cambios = datos.model_dump(exclude_unset=True)
    if (area := cambios.pop("area", None)) is not None:
        proyecto.area = area_por_nombre(db, area)
    if (ods := cambios.pop("ods", None)) is not None:
        proyecto.ods = ods_por_id(db, ods)
    if (actores := cambios.pop("actores", None)) is not None:
        proyecto.actores = _actores(db, actores)
    for campo, valor in cambios.items():
        setattr(proyecto, campo, valor)
    if proyecto.fecha_fin and proyecto.fecha_fin < proyecto.fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha de cierre no puede ser anterior a la de inicio")
    db.commit()
    return ProyectoSalida.de(proyecto)


@router.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proyecto(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    _verificar_dueno(proyecto, usuario)
    db.delete(proyecto)
    db.commit()
