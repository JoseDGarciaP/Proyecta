import uuid
from datetime import date, datetime, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator



class UsuarioAdmin(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str
    rol: str
    rol_nombre: str
    programa: str | None
    activo: bool
    verificado: bool
    con_google: bool
    creado_en: date
    proyectos: int  # proyectos que registró
    colaboraciones: int  # proyectos ajenos donde es miembro


class PaginaUsuarios(BaseModel):
    total: int
    items: list[UsuarioAdmin]


class CambiosUsuario(BaseModel):
    nombre: str | None = Field(default=None, min_length=3, max_length=150)
    programa: str | None = Field(default=None, max_length=150)
    rol: str | None = Field(default=None, max_length=40)
    activo: bool | None = None
    verificado: bool | None = None


class NuevoUsuario(BaseModel):
    # Se valida en app.core.validacion_correo (mensajes claros de tipeo, desechables y DNS).
    email: str = Field(min_length=3, max_length=254)
    nombre: str = Field(min_length=3, max_length=150)
    rol: str = Field(default="estudiante", max_length=40)
    programa: str | None = Field(default=None, max_length=150)


class AreaEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)


class AreaAdmin(BaseModel):
    id: int
    nombre: str
    proyectos: int
    oportunidades: int


class OdsEntrada(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)


class OdsAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str


class Conteo(BaseModel):
    clave: str
    total: int


class UsoMotivo(BaseModel):
    motivo: str
    tipo: str
    total: int


class Estadisticas(BaseModel):
    usuarios_total: int
    usuarios_activos: int
    usuarios_sin_verificar: int
    usuarios_inactivos: int
    usuarios_por_rol: list[Conteo]
    proyectos: int
    oportunidades_abiertas: int
    actores: int
    solicitudes_por_estado: list[Conteo]
    tasa_aprobacion: float | None  # aceptadas / (aceptadas + rechazadas)
    motivos: list[UsoMotivo]
    aportes: list[Conteo]
    correos_30_dias: int
    notificaciones_sin_leer: int


class ProyectoAdmin(BaseModel):
    id: uuid.UUID
    titulo: str
    area: str
    estado: str
    responsable_id: uuid.UUID | None
    responsable_nombre: str | None
    responsable_email: str | None
    miembros: int
    solicitudes_pendientes: int
    creado_en: date


class Eliminacion(BaseModel):
    motivo: str = Field(min_length=5, max_length=500, description="Se le envía a quien registró el proyecto")


class RegistroSalida(BaseModel):
    id: uuid.UUID
    admin_nombre: str
    accion: str
    objeto: str
    detalle: str
    creado_en: datetime

    @field_validator("creado_en")
    @classmethod
    def en_utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)


class ResultadoResumen(BaseModel):
    avisos: int
