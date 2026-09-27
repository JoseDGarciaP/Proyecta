import uuid

from pydantic import BaseModel, Field

from app.modules.actores.models import TipoActor


class ActorEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=200)
    tipo: TipoActor
    sector: str = Field(default="", max_length=150)
    contacto: str = Field(default="", max_length=200)


class ActorSalida(ActorEntrada):
    id: uuid.UUID
    proyectos: int
