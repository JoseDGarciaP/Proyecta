import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import Admin, DbSession
from app.modules.catalogo.models import Area, Ods
from app.modules.catalogo.service import areas_por_nombre, ods_por_id
from app.modules.oportunidades.models import Oportunidad, TipoOportunidad
from app.modules.oportunidades.schemas import OportunidadEntrada, OportunidadSalida

router = APIRouter(prefix="/api/oportunidades", tags=["oportunidades"])


def _obtener(db: Session, oportunidad_id: uuid.UUID) -> Oportunidad:
    oportunidad = db.get(Oportunidad, oportunidad_id)
    if oportunidad is None:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return oportunidad


def _aplicar(db: Session, oportunidad: Oportunidad, datos: OportunidadEntrada) -> None:
    for campo, valor in datos.model_dump(exclude={"areas", "ods"}).items():
        setattr(oportunidad, campo, valor)
    oportunidad.areas = areas_por_nombre(db, datos.areas)
    oportunidad.ods = ods_por_id(db, datos.ods)


@router.get("", response_model=list[OportunidadSalida])
def listar_oportunidades(
    db: DbSession,
    q: str | None = None,
    area: str | None = None,
    ods: int | None = None,
    tipo: TipoOportunidad | None = None,
    abiertas: bool = Query(default=False, description="Solo las que no han cerrado"),
):
    stmt = select(Oportunidad)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(Oportunidad.titulo.ilike(patron), Oportunidad.entidad.ilike(patron),
                              Oportunidad.descripcion.ilike(patron)))
    if area:
        stmt = stmt.where(Oportunidad.areas.any(Area.nombre == area))
    if ods:
        stmt = stmt.where(Oportunidad.ods.any(Ods.id == ods))
    if tipo:
        stmt = stmt.where(Oportunidad.tipo == tipo)
    if abiertas:
        stmt = stmt.where(Oportunidad.cierra_en >= date.today())
    return [OportunidadSalida.de(o) for o in db.scalars(stmt.order_by(Oportunidad.cierra_en))]


@router.get("/{oportunidad_id}", response_model=OportunidadSalida)
def leer_oportunidad(oportunidad_id: uuid.UUID, db: DbSession):
    return OportunidadSalida.de(_obtener(db, oportunidad_id))


@router.post("", response_model=OportunidadSalida, status_code=status.HTTP_201_CREATED)
def crear_oportunidad(datos: OportunidadEntrada, admin: Admin, db: DbSession):
    oportunidad = Oportunidad(creado_por_id=admin.id)
    _aplicar(db, oportunidad, datos)
    db.add(oportunidad)
    db.commit()
    return OportunidadSalida.de(oportunidad)


@router.put("/{oportunidad_id}", response_model=OportunidadSalida)
def actualizar_oportunidad(oportunidad_id: uuid.UUID, datos: OportunidadEntrada, _: Admin, db: DbSession):
    oportunidad = _obtener(db, oportunidad_id)
    _aplicar(db, oportunidad, datos)
    db.commit()
    return OportunidadSalida.de(oportunidad)


@router.delete("/{oportunidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_oportunidad(oportunidad_id: uuid.UUID, _: Admin, db: DbSession):
    db.delete(_obtener(db, oportunidad_id))
    db.commit()
