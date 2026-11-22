import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DatosAliado(BaseModel):
    """Lo que pide el registro de un aliado externo."""

    razon_social: str = Field(default="", max_length=200)
    tipo: str = Field(default="Otro", max_length=60)
    documento: str = Field(min_length=5, max_length=30)
    telefono: str = Field(min_length=7, max_length=30)
    sector: str = Field(min_length=2, max_length=120)


class AliadoActualizar(BaseModel):
    """Lo que el aliado cambia desde su perfil. El documento solo lo cambia un administrador."""

    telefono: str | None = Field(default=None, min_length=7, max_length=30)
    sector: str | None = Field(default=None, min_length=2, max_length=120)
    sitio_web: str | None = Field(default=None, max_length=300)
    descripcion: str | None = Field(default=None, max_length=3000)
    razon_social: str | None = Field(default=None, max_length=200)


class AliadoPropio(BaseModel):
    usuario_id: uuid.UUID
    razon_social: str
    tipo: str
    documento: str | None
    telefono: str
    sector: str
    sitio_web: str
    descripcion: str
    estado: str
    motivo_rechazo: str


class ProyectoApoyado(BaseModel):
    id: uuid.UUID
    titulo: str
    rol: str


class AliadoPublico(BaseModel):
    usuario_id: uuid.UUID
    nombre: str
    razon_social: str
    tipo: str
    sector: str
    sitio_web: str
    descripcion: str
    intereses: list[str]
    proyectos: list[ProyectoApoyado]


class AliadoAdmin(AliadoPropio):
    nombre: str
    email: str
    creado_en: datetime
    revisado_en: datetime | None


class Rechazo(BaseModel):
    motivo: str = Field(min_length=5, max_length=1000)


class DocumentoAdmin(BaseModel):
    documento: str = Field(min_length=5, max_length=30)
