import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc(v: datetime | None) -> datetime | None:
    return v.replace(tzinfo=timezone.utc) if v is not None and v.tzinfo is None else v


class NivelBreve(BaseModel):
    id: int
    nombre: str
    icono: str
    color: str
    posicion: int  # 1 = primer nivel


class NivelEntrada(BaseModel):
    nombre: str = Field(min_length=2, max_length=60)
    descripcion: str = Field(default="", max_length=500)
    icono: str = "star"
    color: str = "slate"
    xp_minima: int = Field(default=0, ge=0, le=10_000_000)
    insignias_minimas: int = Field(default=0, ge=0, le=1000)
    insignias_requeridas: list[int] = Field(default_factory=list, max_length=20)


class NivelSalida(NivelEntrada):
    model_config = ConfigDict(from_attributes=True)
    id: int
    posicion: int = 0
    personas: int = 0


class Siguiente(BaseModel):
    nivel: NivelSalida
    xp_faltante: int
    insignias_faltantes: int
    requeridas_faltantes: list[str]  # nombres de insignias obligatorias que aún no tiene


class MovimientoSalida(BaseModel):
    id: uuid.UUID
    accion: str
    accion_nombre: str
    puntos: int
    detalle: str
    otorgado_por: str | None
    creado_en: datetime

    @field_validator("creado_en")
    @classmethod
    def en_utc(cls, v: datetime) -> datetime:
        return _utc(v)


class AccionEntrada(BaseModel):
    nombre: str = Field(min_length=3, max_length=120)
    descripcion: str = Field(default="", max_length=500)
    puntos: int = Field(ge=0, le=100_000)
    tope_diario: int | None = Field(default=None, ge=1, le=1000)
    activo: bool = True


class AccionSalida(AccionEntrada):
    model_config = ConfigDict(from_attributes=True)
    clave: str
    orden: int


class MiExperiencia(BaseModel):
    xp: int
    xp_semana: int
    nivel: NivelBreve | None
    siguiente: Siguiente | None
    total_niveles: int
    historial: list[MovimientoSalida]
    acciones: list[AccionSalida]


class ExperienciaBreve(BaseModel):
    xp: int
    nivel: NivelBreve | None


class PuestoXP(BaseModel):
    posicion: int
    usuario_id: uuid.UUID
    nombre: str
    rol_nombre: str
    programa: str | None
    xp: int  # en el periodo
    xp_total: int
    nivel: NivelBreve | None


class Ajuste(BaseModel):
    usuario_id: uuid.UUID
    puntos: int = Field(ge=-100_000, le=100_000)
    motivo: str = Field(min_length=5, max_length=500)

    @field_validator("puntos")
    @classmethod
    def no_cero(cls, v: int) -> int:
        if v == 0:
            raise ValueError("Los puntos no pueden ser 0")
        return v


class PersonaXP(BaseModel):
    id: uuid.UUID
    nombre: str
    email: str
    rol_nombre: str
    xp: int
    nivel: NivelBreve | None


class ResumenUsuarioXP(BaseModel):
    usuario_id: uuid.UUID
    nombre: str
    xp: int
    nivel: NivelBreve | None
    historial: list[MovimientoSalida]
