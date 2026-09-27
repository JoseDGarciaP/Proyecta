from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.catalogo.models import Area, Ods


def area_por_nombre(db: Session, nombre: str) -> Area:
    area = db.scalar(select(Area).where(Area.nombre == nombre))
    if area is None:
        raise HTTPException(status_code=422, detail=f"El área '{nombre}' no existe")
    return area


def areas_por_nombre(db: Session, nombres: list[str]) -> list[Area]:
    return [area_por_nombre(db, n) for n in dict.fromkeys(nombres)]


def ods_por_id(db: Session, ids: list[int]) -> list[Ods]:
    items = db.scalars(select(Ods).where(Ods.id.in_(ids))).all() if ids else []
    if len(items) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Algún ODS no existe")
    return list(items)
