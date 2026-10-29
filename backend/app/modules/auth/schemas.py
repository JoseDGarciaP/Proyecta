from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.core.security import validar_contrasena

# Contraseña nueva: 8 a 20 caracteres con mayúscula, minúscula, número y símbolo.
ContrasenaNueva = Annotated[str, AfterValidator(validar_contrasena)]



class Registro(BaseModel):
    # Se valida en app.core.validacion_correo para dar mensajes claros (tipeo, desechables, DNS).
    email: str = Field(min_length=3, max_length=254)
    password: ContrasenaNueva
    nombre: str = Field(min_length=3, max_length=150)
    rol: str = Field(default="estudiante", max_length=40)
    programa: str | None = Field(default=None, max_length=150)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Verificacion(BaseModel):
    token: str


class Reenvio(BaseModel):
    email: EmailStr


class Restablecer(BaseModel):
    token: str
    password: ContrasenaNueva


class IngresoGoogle(BaseModel):
    credential: str  # ID token que entrega el botón de Google Identity Services


class ConfigAuth(BaseModel):
    google_client_id: str | None
    dominios: list[str]
