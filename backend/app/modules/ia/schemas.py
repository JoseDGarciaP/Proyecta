import uuid

from typing import Literal

from pydantic import BaseModel


class Recomendacion(BaseModel):
    oportunidad_id: uuid.UUID
    titulo: str
    puntaje: float
    razon: str


class RespuestaAnalisis(BaseModel):
    resumen: str
    recomendaciones: list[Recomendacion]
    simulado: bool  # True cuando el resumen sale de la heurística y no de un modelo


class Sugerencia(BaseModel):
    """Un resultado de similitud: proyecto, oportunidad o persona."""

    id: uuid.UUID
    tipo: Literal["proyecto", "oportunidad", "usuario"]
    titulo: str
    detalle: str
    similitud: float
    razon: str


class RespuestaSugerencias(BaseModel):
    metodo: Literal["semantico", "lexico"]  # léxico = sin modelo de embeddings disponible
    resultados: list[Sugerencia]


class SugerenciasParaMi(BaseModel):
    metodo: Literal["semantico", "lexico"]
    perfil_completo: bool  # False si faltan habilidades o intereses para comparar
    proyectos: list[Sugerencia]  # proyectos que buscan un perfil como el mío
    oportunidades: list[Sugerencia]  # oportunidades para los proyectos donde participo
