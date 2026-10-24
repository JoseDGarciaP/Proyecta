import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.notificaciones.models import TipoNotificacion


class NotificacionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoNotificacion
    titulo: str
    cuerpo: str
    enlace: str
    leida: bool
    correo_enviado: bool
    creada_en: datetime

    @field_validator("creada_en")
    @classmethod
    def en_utc(cls, v: datetime) -> datetime:
        """SQLite devuelve fechas sin zona; se guardan en UTC, así que se marcan como UTC."""
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class Conteo(BaseModel):
    no_leidas: int


class PreferenciasCorreo(BaseModel):
    solicitudes: bool = True
    respuestas: bool = True
    mensajes: bool = True
    logros: bool = True
