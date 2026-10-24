import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session

from app.core.deps import DbSession, UsuarioActual, requiere
from app.modules.actores.models import Actor
from app.modules.catalogo.models import Area, Ods
from app.modules.catalogo.service import area_por_nombre, ods_por_id
from app.modules.proyectos.models import Estado, Proyecto
from app.modules.proyectos.schemas import ProyectoActualizar, ProyectoEntrada, ProyectoSalida
from app.modules.roles.servicio import puede
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/proyectos", tags=["proyectos"])


def obtener_proyecto(db: Session, proyecto_id: uuid.UUID) -> Proyecto:
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto


def _verificar_dueno(db: Session, proyecto: Proyecto, usuario: Usuario) -> None:
    if proyecto.creado_por_id != usuario.id and not puede(db, usuario, "proyectos.moderar"):
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto puede modificarlo")


def _actores(db: Session, ids: list[uuid.UUID]) -> list[Actor]:
    items = db.scalars(select(Actor).where(Actor.id.in_(ids))).all() if ids else []
    if len(items) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Algún actor no existe")
    return list(items)


def _evaluar_logros(db: Session, proyecto: Proyecto, tareas: BackgroundTasks) -> None:
    from app.modules.alianzas.models import Miembro
    from app.modules.insignias.servicio import evaluar_ids

    miembros = db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id)).all()
    evaluar_ids(db, [proyecto.creado_por_id, *miembros], tareas)


def _experiencia(db: Session, proyecto: Proyecto, avance_antes: int, estado_antes, tareas: BackgroundTasks) -> None:
    """XP para el equipo cuando el avance cruza otra decena (10 %, 20 %…) y cuando el proyecto finaliza."""
    from app.modules.alianzas.models import Miembro
    from app.modules.experiencia.servicio import sumar_a_varios

    equipo = [proyecto.creado_por_id, *db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id))]
    for decena in range(avance_antes // 10 + 1, proyecto.avance // 10 + 1):
        sumar_a_varios(db, equipo, "proyecto_avanza", f"{proyecto.id}:{decena * 10}", f"«{proyecto.titulo}» llegó al {decena * 10} %", tareas)
    if proyecto.estado == Estado.FINALIZADO and estado_antes != Estado.FINALIZADO:
        sumar_a_varios(db, equipo, "proyecto_finalizado", str(proyecto.id), f"«{proyecto.titulo}» finalizado", tareas)


@router.get("", response_model=list[ProyectoSalida])
def listar_proyectos(
    db: DbSession,
    q: str | None = Query(default=None, description="Busca en título, resumen, líder y etiquetas"),
    area: str | None = None,
    estado: Estado | None = None,
    ods: int | None = None,
    limit: int = Query(default=200, le=500),
    offset: int = 0,
):
    stmt = select(Proyecto)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(
            Proyecto.titulo.ilike(patron), Proyecto.resumen.ilike(patron),
            Proyecto.lider.ilike(patron), cast(Proyecto.etiquetas, String).ilike(patron),
        ))
    if area:
        stmt = stmt.join(Proyecto.area).where(Area.nombre == area)
    if estado:
        stmt = stmt.where(Proyecto.estado == estado)
    if ods:
        stmt = stmt.where(Proyecto.ods.any(Ods.id == ods))
    orden = stmt.order_by(Proyecto.creado_en.desc(), Proyecto.actualizado_en.desc()).limit(limit).offset(offset)
    return [ProyectoSalida.de(p) for p in db.scalars(orden).unique()]


@router.post("", response_model=ProyectoSalida, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requiere("proyectos.crear"))])
def crear_proyecto(datos: ProyectoEntrada, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    proyecto = Proyecto(
        **datos.model_dump(exclude={"area", "ods", "actores", "lider"}),
        lider=datos.lider.strip() or usuario.nombre,
        creado_por_id=usuario.id,
    )
    proyecto.area = area_por_nombre(db, datos.area)
    proyecto.ods = ods_por_id(db, datos.ods)
    proyecto.actores = _actores(db, datos.actores)
    db.add(proyecto)
    db.flush()
    from app.modules.experiencia.servicio import sumar
    sumar(db, usuario, "proyecto_registrado", str(proyecto.id), f"Registró «{proyecto.titulo}»", tareas)
    _evaluar_logros(db, proyecto, tareas)
    db.commit()
    return ProyectoSalida.de(proyecto)


@router.get("/{proyecto_id}", response_model=ProyectoSalida)
def leer_proyecto(proyecto_id: uuid.UUID, db: DbSession):
    return ProyectoSalida.de(obtener_proyecto(db, proyecto_id))


@router.patch("/{proyecto_id}", response_model=ProyectoSalida)
def actualizar_proyecto(proyecto_id: uuid.UUID, datos: ProyectoActualizar, usuario: UsuarioActual, db: DbSession,
                        tareas: BackgroundTasks):
    proyecto = obtener_proyecto(db, proyecto_id)
    _verificar_dueno(db, proyecto, usuario)
    cambios = datos.model_dump(exclude_unset=True)
    avance_antes, estado_antes = proyecto.avance, proyecto.estado
    if (area := cambios.pop("area", None)) is not None:
        proyecto.area = area_por_nombre(db, area)
    if (ods := cambios.pop("ods", None)) is not None:
        proyecto.ods = ods_por_id(db, ods)
    if (actores := cambios.pop("actores", None)) is not None:
        proyecto.actores = _actores(db, actores)
    for campo, valor in cambios.items():
        setattr(proyecto, campo, valor)
    if proyecto.fecha_fin and proyecto.fecha_fin < proyecto.fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha de cierre no puede ser anterior a la de inicio")
    db.flush()
    _experiencia(db, proyecto, avance_antes, estado_antes, tareas)
    _evaluar_logros(db, proyecto, tareas)  # p. ej. «Proyecto cumplido» para todo el equipo
    db.commit()
    return ProyectoSalida.de(proyecto)


@router.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proyecto(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    proyecto = obtener_proyecto(db, proyecto_id)
    _verificar_dueno(db, proyecto, usuario)
    db.delete(proyecto)
    db.commit()
