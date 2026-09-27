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
    settings = get_settings()
    modelo = {"ollama": settings.ollama_model, "anthropic": settings.anthropic_model}.get(settings.ia_proveedor)
    return {"proveedor": settings.ia_proveedor, "modelo": modelo}


@router.post("/proyectos/{proyecto_id}/analisis", response_model=RespuestaAnalisis)
async def analizar_proyecto(proyecto_id: uuid.UUID, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    oportunidades = list(db.scalars(select(Oportunidad)))
    return await analizar(proyecto, oportunidades)
