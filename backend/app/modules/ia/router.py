import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DbSession
from app.modules.ia.schemas import RespuestaAnalisis
from app.modules.ia.servicio import analizar
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.router import obtener_proyecto

router = APIRouter(prefix="/api/ia", tags=["inteligencia artificial"])


@router.get("/estado")
def estado():
    return {"modelo_configurado": bool(get_settings().anthropic_api_key)}


@router.post("/proyectos/{proyecto_id}/analisis", response_model=RespuestaAnalisis)
async def analizar_proyecto(proyecto_id: uuid.UUID, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    oportunidades = list(db.scalars(select(Oportunidad)))
    return await analizar(proyecto, oportunidades)
