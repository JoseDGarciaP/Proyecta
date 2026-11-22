import uuid
from datetime import datetime

from typing import Literal

from pydantic import BaseModel, Field


class Recomendacion(BaseModel):
    oportunidad_id: uuid.UUID
    titulo: str
    puntaje: float
    razon: str
    # Registro guardado de la recomendación (HU-05): se llenan al guardarla.
    recomendacion_id: uuid.UUID | None = None
    estado: Literal["pendiente", "aceptada", "anulada"] = "pendiente"
    fecha: datetime | None = None


class RespuestaAnalisis(BaseModel):
    resumen: str
    recomendaciones: list[Recomendacion]
    fortalezas: list[str] = []
    pasos_sugeridos: list[str] = []
    simulado: bool  # True cuando el resumen sale de la heurística y no de un modelo
    # Ep5-Hu9: proyectos parecidos en los que se apoyan las mejoras sugeridas.
    similares: list["Sugerencia"] = []


class RespuestaPitch(BaseModel):
    """Borrador de carta de postulación de un proyecto a una oportunidad de apoyo."""

    pitch: str
    puntos_clave: list[str] = []
    simulado: bool


class Sugerencia(BaseModel):
    """Un resultado de similitud: proyecto, oportunidad o persona."""

    id: uuid.UUID
    tipo: Literal["proyecto", "oportunidad", "usuario"]
    titulo: str
    detalle: str
    similitud: float
    razon: str
    # Solo en colaboradores sugeridos a un proyecto: registro guardado (HU-05).
    recomendacion_id: uuid.UUID | None = None
    estado: Literal["pendiente", "aceptada", "anulada"] | None = None
    fecha: datetime | None = None


class RespuestaSugerencias(BaseModel):
    metodo: Literal["semantico", "lexico"]  # léxico = sin modelo de embeddings disponible
    resultados: list[Sugerencia]


class RecomendacionSalida(BaseModel):
    """Recomendación guardada de un proyecto, con su fecha y estado (HU-05)."""

    id: uuid.UUID
    proyecto_id: uuid.UUID
    tipo: Literal["oportunidad", "colaborador"]
    objetivo_id: uuid.UUID
    titulo: str
    puntaje: float
    razon: str
    estado: Literal["pendiente", "aceptada", "anulada"]
    creado_en: datetime
    motivo: str = ""
    decidido_en: datetime | None = None


class SugerenciasParaMi(BaseModel):
    metodo: Literal["semantico", "lexico"]
    perfil_completo: bool  # False si faltan habilidades o intereses para comparar
    proyectos: list[Sugerencia]  # proyectos que buscan un perfil como el mío
    oportunidades: list[Sugerencia]  # oportunidades para los proyectos donde participo


class Anular(BaseModel):
    motivo: str = Field(min_length=5, max_length=1000)


class Valoracion(BaseModel):
    util: bool
    comentario: str = Field(default="", max_length=1000)


class ResumenValoraciones(BaseModel):
    utiles: int
    no_utiles: int
    mia: bool | None  # lo que marcó quien consulta, si ya valoró


RespuestaAnalisis.model_rebuild()
