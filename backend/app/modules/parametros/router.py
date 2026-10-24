from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import DbSession
from app.modules.parametros.models import Motivo, Plantilla, TipoAporte
from app.modules.parametros.schemas import ParametrosColaboracion

router = APIRouter(prefix="/api/parametros", tags=["parámetros"])


@router.get("/colaboracion", response_model=ParametrosColaboracion)
def parametros_colaboracion(db: DbSession):
    return ParametrosColaboracion(
        motivos=db.scalars(select(Motivo).where(Motivo.activo.is_(True)).order_by(Motivo.tipo, Motivo.orden, Motivo.id)).all(),
        tipos_aporte=db.scalars(select(TipoAporte).where(TipoAporte.activo.is_(True)).order_by(TipoAporte.orden, TipoAporte.nombre)).all(),
        plantillas=db.scalars(select(Plantilla).where(Plantilla.activo.is_(True)).order_by(Plantilla.orden, Plantilla.id)).all(),
    )
