import uuid
from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.modules.proyectos.models import Estado, Proyecto


class ProyectoEntrada(BaseModel):
    titulo: str = Field(min_length=5, max_length=200)
    resumen: str = Field(min_length=10, max_length=300)
    descripcion: str = ""
    necesidades: str = ""
    area: str
    estado: Estado = Estado.IDEA
    avance: int = Field(default=0, ge=0, le=100)
    presupuesto: int = Field(default=0, ge=0)
    lider: str = Field(default="", max_length=150)  # vacío = nombre de quien registra
    equipo: list[str] = []
    etiquetas: list[str] = []
    fecha_inicio: date = Field(default_factory=date.today)
    fecha_fin: date | None = None
    ods: list[int] = []
    actores: list[uuid.UUID] = []

    @model_validator(mode="after")
    def fechas(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de cierre no puede ser anterior a la de inicio")
        return self


class ProyectoActualizar(BaseModel):
    titulo: str | None = Field(default=None, min_length=5, max_length=200)
    resumen: str | None = Field(default=None, min_length=10, max_length=300)
    descripcion: str | None = None
    necesidades: str | None = None
    area: str | None = None
    estado: Estado | None = None
    avance: int | None = Field(default=None, ge=0, le=100)
    presupuesto: int | None = Field(default=None, ge=0)
    lider: str | None = Field(default=None, max_length=150)
    equipo: list[str] | None = None
    etiquetas: list[str] | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    ods: list[int] | None = None
    actores: list[uuid.UUID] | None = None


class ProyectoSalida(BaseModel):
    """Mismo formato que la interfaz `Proyecto` de src/lib/types.ts."""

    id: uuid.UUID
    titulo: str
    resumen: str
    descripcion: str
    necesidades: str
    area: str
    estado: Estado
    avance: int
    presupuesto: int
    lider: str
    equipo: list[str]
    etiquetas: list[str]
    fecha_inicio: date
    fecha_fin: date | None
    actores: list[uuid.UUID]
    ods: list[int]
    creado_por: uuid.UUID | None
    creado_en: date

    @classmethod
    def de(cls, p: Proyecto) -> "ProyectoSalida":
        return cls(
            id=p.id, titulo=p.titulo, resumen=p.resumen, descripcion=p.descripcion, necesidades=p.necesidades,
            area=p.area.nombre, estado=p.estado, avance=p.avance, presupuesto=p.presupuesto, lider=p.lider,
            equipo=p.equipo, etiquetas=p.etiquetas, fecha_inicio=p.fecha_inicio, fecha_fin=p.fecha_fin,
            actores=[a.id for a in p.actores], ods=sorted(o.id for o in p.ods),
            creado_por=p.creado_por_id, creado_en=p.creado_en,
        )
