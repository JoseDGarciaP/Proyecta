"""Guarda las recomendaciones de la IA con su fecha y estado (HU-05).

Cada vez que se generan recomendaciones para un proyecto se registran como «pendiente».
Si la misma oportunidad o persona ya estaba recomendada y sigue pendiente, se actualizan su
puntaje y su explicación en lugar de duplicarla; si ya fue aceptada o anulada, se respeta ese estado.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ia.models import EstadoRecomendacion, RecomendacionGuardada, TipoRecomendacion


@dataclass
class Item:
    objetivo_id: uuid.UUID
    titulo: str
    puntaje: float
    razon: str


def guardar(db: Session, proyecto_id: uuid.UUID, tipo: TipoRecomendacion, items: list[Item]) -> dict[uuid.UUID, RecomendacionGuardada]:
    """Registra las recomendaciones y devuelve el registro de cada una por `objetivo_id`."""
    if not items:
        return {}
    existentes: dict[uuid.UUID, RecomendacionGuardada] = {}
    for r in db.scalars(
        select(RecomendacionGuardada)
        .where(RecomendacionGuardada.proyecto_id == proyecto_id, RecomendacionGuardada.tipo == tipo,
               RecomendacionGuardada.objetivo_id.in_([i.objetivo_id for i in items]))
        .order_by(RecomendacionGuardada.creado_en.desc())
    ):
        existentes.setdefault(r.objetivo_id, r)  # la más reciente

    salida: dict[uuid.UUID, RecomendacionGuardada] = {}
    for item in items:
        registro = existentes.get(item.objetivo_id)
        if registro is None:
            registro = RecomendacionGuardada(
                proyecto_id=proyecto_id, tipo=tipo, objetivo_id=item.objetivo_id,
                estado=EstadoRecomendacion.PENDIENTE,
            )
            db.add(registro)
        if registro.estado == EstadoRecomendacion.PENDIENTE:
            registro.titulo = item.titulo[:200]
            registro.puntaje = item.puntaje
            registro.razon = item.razon
        salida[item.objetivo_id] = registro
    db.commit()
    return salida
