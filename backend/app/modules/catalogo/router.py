from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import DbSession
from app.modules.catalogo.models import Area, Ods
from app.modules.catalogo.schemas import ItemCatalogo

router = APIRouter(prefix="/api/catalogo", tags=["catálogo"])


@router.get("/areas", response_model=list[ItemCatalogo])
def listar_areas(db: DbSession):
    return db.scalars(select(Area).order_by(Area.nombre)).all()


@router.get("/ods", response_model=list[ItemCatalogo])
def listar_ods(db: DbSession):
    return db.scalars(select(Ods).order_by(Ods.id)).all()
