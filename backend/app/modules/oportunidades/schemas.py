import uuid
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.modules.oportunidades.models import Oportunidad, TipoOportunidad


class OportunidadEntrada(BaseModel):
    titulo: str = Field(min_length=5, max_length=200)
    entidad: str = Field(default="", max_length=150)
    tipo: TipoOportunidad
    descripcion: str = ""
    monto: int | None = Field(default=None, ge=0)
    abre_en: date = Field(default_factory=date.today)
    cierra_en: date
    url: str = Field(default="", max_length=500)
    areas: list[str] = []
    ods: list[int] = []

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.cierra_en <= self.abre_en:
            raise ValueError("La fecha de cierre debe ser mayor a la fecha de apertura")
        return self


class OportunidadSalida(BaseModel):
    """Mismo formato que la interfaz `Oportunidad` de src/lib/types.ts."""

    id: uuid.UUID
    titulo: str
    entidad: str = ""
    tipo: TipoOportunidad
    descripcion: str = ""
    monto: int | None = None
    abre_en: date
    cierra_en: date
    url: str = ""
    areas: list[str] = []
    ods: list[int] = []
    dias_restantes: int = 0  # días que faltan para el cierre (negativo si ya cerró) (HU-04)

    @classmethod
    def de(cls, o: Oportunidad) -> "OportunidadSalida":
        return cls(
            id=o.id, titulo=o.titulo, entidad=o.entidad, tipo=o.tipo, descripcion=o.descripcion, monto=o.monto,
            abre_en=o.abre_en, cierra_en=o.cierra_en, url=o.url, areas=[a.nombre for a in o.areas],
            ods=sorted(x.id for x in o.ods), dias_restantes=(o.cierra_en - date.today()).days,
        )
