"""Lo único que ve un visitante sin cuenta: cifras generales para la página de inicio."""

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.deps import DbSession
from app.modules.actores.models import Actor
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/publico", tags=["público"])


class Cifras(BaseModel):
    proyectos: int
    actores: int
    oportunidades_abiertas: int
    personas: int


@router.get("/cifras", response_model=Cifras)
def cifras(db: DbSession):
    contar = lambda stmt: db.scalar(stmt) or 0  # noqa: E731
    return Cifras(
        proyectos=contar(select(func.count(Proyecto.id))),
        actores=contar(select(func.count(Actor.id))),
        oportunidades_abiertas=contar(select(func.count(Oportunidad.id)).where(Oportunidad.cierra_en >= date.today())),
        personas=contar(select(func.count(Usuario.id)).where(Usuario.verificado.is_(True))),
    )
