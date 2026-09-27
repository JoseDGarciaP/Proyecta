import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.usuarios.models import Rol


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    rol: Rol
    programa: str | None
    bio: str | None
    habilidades: list[str]
    intereses: list[str]


class UsuarioPropio(UsuarioPublico):
    email: EmailStr


class UsuarioActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=150)
    programa: str | None = Field(default=None, max_length=150)
    bio: str | None = None
    habilidades: list[str] | None = None
    intereses: list[str] | None = None
