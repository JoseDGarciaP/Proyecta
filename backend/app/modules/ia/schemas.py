import uuid

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
