import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.modules.oportunidades.models import Oportunidad, TipoOportunidad


class OportunidadEntrada(BaseModel):
    titulo: str = Field(min_length=5, max_length=200)
    entidad: str = Field(default="", max_length=150)
    tipo: TipoOportunidad
    descripcion: str = ""
    monto: int | None = Field(default=None, ge=0)
    cierra_en: date
    url: str = Field(default="", max_length=500)
    areas: list[str] = []
    ods: list[int] = []


class OportunidadSalida(OportunidadEntrada):
    """Mismo formato que la interfaz `Oportunidad` de src/lib/types.ts."""

    id: uuid.UUID

    @classmethod
    def de(cls, o: Oportunidad) -> "OportunidadSalida":
        return cls(
            id=o.id, titulo=o.titulo, entidad=o.entidad, tipo=o.tipo, descripcion=o.descripcion, monto=o.monto,
            cierra_en=o.cierra_en, url=o.url, areas=[a.nombre for a in o.areas], ods=sorted(x.id for x in o.ods),
        )
