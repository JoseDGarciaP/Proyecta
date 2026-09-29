from pydantic import BaseModel, EmailStr, Field

from app.modules.usuarios.models import Rol


class Registro(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    nombre: str = Field(min_length=3, max_length=150)
    rol: Rol = Rol.ESTUDIANTE
    programa: str | None = Field(default=None, max_length=150)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Verificacion(BaseModel):
    token: str


class Reenvio(BaseModel):
    email: EmailStr


class IngresoGoogle(BaseModel):
    credential: str  # ID token que entrega el botón de Google Identity Services


class ConfigAuth(BaseModel):
    google_client_id: str | None
    dominios: list[str]
