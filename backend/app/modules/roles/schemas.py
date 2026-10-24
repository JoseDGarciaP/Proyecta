from pydantic import BaseModel, ConfigDict, Field


class PermisoSalida(BaseModel):
    clave: str
    grupo: str
    nombre: str
    descripcion: str
    solo_admin: bool


class RolEntrada(BaseModel):
    nombre: str = Field(min_length=3, max_length=80)
    descripcion: str = Field(default="", max_length=500)
    institucional: bool = True
    registro_publico: bool = False
    permisos: list[str] = Field(default_factory=list)


class RolSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clave: str
    nombre: str
    descripcion: str
    institucional: bool
    registro_publico: bool
    sistema: bool
    permisos: list[str]
    orden: int
    usuarios: int = 0


class RolBreve(BaseModel):
    """Lo que necesitan los selectores (registro, filtros, crear usuario)."""

    model_config = ConfigDict(from_attributes=True)

    clave: str
    nombre: str
    descripcion: str
    institucional: bool
