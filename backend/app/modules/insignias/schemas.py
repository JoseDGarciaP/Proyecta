import uuid
from datetime import date, datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _utc(v: datetime | None) -> datetime | None:
    return v.replace(tzinfo=timezone.utc) if v is not None and v.tzinfo is None else v


class Condicion(BaseModel):
    criterio: str
    umbral: int = Field(default=1, ge=1, le=100000)
    valor: str | None = Field(default=None, max_length=120)  # área, número de ODS, clave de rol o texto


class Reglas(BaseModel):
    modo: Literal["todas", "alguna"] = "todas"
    condiciones: list[Condicion] = Field(min_length=1, max_length=8)


class InsigniaEntrada(BaseModel):
    nombre: str = Field(min_length=3, max_length=80)
    descripcion: str = Field(default="", max_length=500)
    tipo: Literal["logro", "condecoracion", "reconocimiento"] = "logro"
    entidad: str = Field(default="", max_length=150)
    icono: str = "award"
    color: str = "amber"
    reglas: Reglas | None = None  # None = la otorga la administración
    vence_en: date | None = None
    vigencia_dias: int | None = Field(default=None, ge=1, le=3650)
    activo: bool = True
    orden: int = 0


class InsigniaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    tipo: str
    entidad: str
    icono: str
    color: str
    reglas: Reglas | None
    vence_en: date | None
    vigencia_dias: int | None
    activo: bool
    orden: int
    automatica: bool
    texto_regla: str = ""
    otorgadas: int = 0  # personas que la tienen vigente


class InsigniaBreve(BaseModel):
    """Para mostrar junto al nombre de una persona y en sus logros."""

    id: int
    nombre: str
    descripcion: str
    tipo: str
    entidad: str
    icono: str
    color: str
    motivo: str
    automatica: bool
    otorgada_en: datetime
    fecha_evento: date | None
    vence_en: datetime | None

    @field_validator("otorgada_en", "vence_en")
    @classmethod
    def en_utc(cls, v: datetime | None) -> datetime | None:
        return _utc(v)

    @classmethod
    def de(cls, f) -> "InsigniaBreve":
        i = f.insignia
        return cls(id=i.id, nombre=i.nombre, descripcion=i.descripcion, tipo=i.tipo, entidad=i.entidad, icono=i.icono,
                   color=i.color, motivo=f.motivo, automatica=f.automatica, otorgada_en=f.otorgada_en,
                   fecha_evento=f.fecha_evento, vence_en=f.vence_en)


class ProgresoCondicion(BaseModel):
    texto: str
    actual: int
    umbral: int


class EnProgreso(BaseModel):
    insignia: InsigniaSalida
    modo: str
    condiciones: list[ProgresoCondicion]
    avance: float  # 0 a 1


class MisLogros(BaseModel):
    obtenidas: list[InsigniaBreve]
    en_progreso: list[EnProgreso]
    manuales_disponibles: list[InsigniaSalida]  # las que solo otorga un administrador
    vencidas: list[InsigniaBreve]


class CriterioSalida(BaseModel):
    clave: str
    nombre: str
    unidad: str
    valor: str | None
    binario: bool
    grupo: str


class Opciones(BaseModel):
    criterios: list[CriterioSalida]
    iconos: list[str]
    colores: list[str]
    tipos: dict[str, str]


class PuestoRanking(BaseModel):
    posicion: int
    usuario_id: uuid.UUID
    nombre: str
    rol_nombre: str
    programa: str | None
    total: int
    insignias: list[InsigniaBreve]


class Otorgamiento(BaseModel):
    usuario_id: uuid.UUID
    motivo: str = Field(min_length=5, max_length=500)
    fecha_evento: date | None = None
    vence_en: date | None = None  # reemplaza la vigencia de la insignia para esta entrega


class OtorgamientoVarios(BaseModel):
    usuario_ids: list[uuid.UUID] = Field(default_factory=list, max_length=300)
    proyecto_id: uuid.UUID | None = None  # suma a quien lo registró y a todos sus miembros
    motivo: str = Field(min_length=5, max_length=500)
    fecha_evento: date | None = None
    vence_en: date | None = None


class ResultadoVarios(BaseModel):
    otorgadas: list[str]  # nombres
    ya_tenian: list[str]


class OtorgadaSalida(BaseModel):
    usuario_id: uuid.UUID
    nombre: str
    email: str
    motivo: str
    automatica: bool
    otorgada_por: str | None
    otorgada_en: datetime
    fecha_evento: date | None
    vence_en: datetime | None
    retirada_en: datetime | None
    estado: Literal["vigente", "vencida", "retirada"]

    @field_validator("otorgada_en", "retirada_en", "vence_en")
    @classmethod
    def en_utc(cls, v: datetime | None) -> datetime | None:
        return _utc(v)


class Evaluacion(BaseModel):
    otorgadas: int
