import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.core.deps import Admin, DbSession
from app.modules.actores.models import Actor, proyecto_actores
from app.modules.actores.schemas import ActorEntrada, ActorSalida

router = APIRouter(prefix="/api/actores", tags=["actores"])


def _salida(actor: Actor, proyectos: int) -> ActorSalida:
    return ActorSalida(id=actor.id, nombre=actor.nombre, tipo=actor.tipo, sector=actor.sector,
                       contacto=actor.contacto, proyectos=proyectos)


def _conteo(db: DbSession, actor_id: uuid.UUID) -> int:
    return db.scalar(select(func.count()).where(proyecto_actores.c.actor_id == actor_id)) or 0


@router.get("", response_model=list[ActorSalida])
def listar_actores(db: DbSession):
    conteo = (
        select(proyecto_actores.c.actor_id, func.count().label("n"))
        .group_by(proyecto_actores.c.actor_id)
        .subquery()
    )
    filas = db.execute(
        select(Actor, func.coalesce(conteo.c.n, 0))
        .outerjoin(conteo, conteo.c.actor_id == Actor.id)
        .order_by(Actor.nombre)
    ).all()
    return [_salida(actor, n) for actor, n in filas]


@router.post("", response_model=ActorSalida, status_code=status.HTTP_201_CREATED)
def crear_actor(datos: ActorEntrada, _: Admin, db: DbSession):
    actor = Actor(**datos.model_dump())
    db.add(actor)
    db.commit()
    return _salida(actor, 0)


@router.put("/{actor_id}", response_model=ActorSalida)
def actualizar_actor(actor_id: uuid.UUID, datos: ActorEntrada, _: Admin, db: DbSession):
    actor = db.get(Actor, actor_id)
    if actor is None:
        raise HTTPException(status_code=404, detail="Actor no encontrado")
    for campo, valor in datos.model_dump().items():
        setattr(actor, campo, valor)
    db.commit()
    return _salida(actor, _conteo(db, actor.id))


@router.delete("/{actor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_actor(actor_id: uuid.UUID, _: Admin, db: DbSession):
    actor = db.get(Actor, actor_id)
    if actor is None:
        raise HTTPException(status_code=404, detail="Actor no encontrado")
    db.delete(actor)
    db.commit()
