import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.chat.models import MensajeBase


class MensajeEntrada(BaseModel):
    texto: str = Field(max_length=2000)

    @field_validator("texto")
    @classmethod
    def no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El mensaje está vacío")
        return v.strip()


class Leido(BaseModel):
    hasta_id: int = Field(ge=0)


class MensajeSalida(BaseModel):
    id: int
    proyecto_id: uuid.UUID | None  # chat del equipo
    solicitud_id: uuid.UUID | None  # conversación de una solicitud
    autor_id: uuid.UUID | None
    autor_nombre: str
    texto: str
    enviado_en: datetime
    editado_en: datetime | None
    eliminado: bool
    modificado_en: datetime
    propio: bool  # True si lo escribió quien consulta

    @classmethod
    def de(cls, m: MensajeBase, yo: uuid.UUID) -> "MensajeSalida":
        return cls(
            id=m.id, proyecto_id=getattr(m, "proyecto_id", None), solicitud_id=getattr(m, "solicitud_id", None),
            autor_id=m.autor_id, autor_nombre=m.autor.nombre if m.autor else "Usuario eliminado",
            texto="" if m.eliminado else m.texto, enviado_en=m.enviado_en, editado_en=m.editado_en,
            eliminado=m.eliminado, modificado_en=m.modificado_en, propio=m.autor_id == yo,
        )


class ResumenChat(BaseModel):
    """Un chat de la lista «mis chats»: de qué es, cuántos mensajes sin leer y el último."""

    tipo: Literal["proyecto", "solicitud"]
    proyecto_id: uuid.UUID
    proyecto_titulo: str
    solicitud_id: uuid.UUID | None
    titulo: str  # el proyecto, o «Persona · Proyecto» en una solicitud
    no_leidos: int
    ultimo: MensajeSalida | None
