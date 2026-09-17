from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Proyecto(BaseModel):
    id: str
    titulo: str
    resumen: str = ""
    descripcion: str = ""
    area: str
    estado: str
    avance: int = 0
    presupuesto: int = 0
    lider: str = ""
    equipo: list[str] = Field(default_factory=list)
    etiquetas: list[str] = Field(default_factory=list)
    actores: list[str] = Field(default_factory=list)


class Oportunidad(BaseModel):
    id: str
    titulo: str
    entidad: str = ""
    tipo: Literal["convocatoria", "financiacion", "mentoria", "infraestructura"]
    monto: int | None = None
    cierra_en: str
    areas: list[str] = Field(default_factory=list)
    url: str = ""


class SolicitudAnalisis(BaseModel):
    proyecto: Proyecto
    oportunidades: list[Oportunidad] = Field(default_factory=list)


class Recomendacion(BaseModel):
    oportunidad_id: str
    titulo: str
    puntaje: float
    razon: str


class RespuestaAnalisis(BaseModel):
    resumen: str
    recomendaciones: list[Recomendacion]
    simulado: bool
