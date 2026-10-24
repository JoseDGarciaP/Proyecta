"""Experiencia (XP) y niveles.

`sumar` registra un movimiento (respetando el tope diario de la acción y sin repetir la misma
referencia), actualiza la XP de la persona y recalcula su nivel. Al subir de nivel avisa.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

from fastapi import BackgroundTasks
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.modules.experiencia.models import AccionXP, MovimientoXP, Nivel
from app.modules.usuarios.models import Usuario

log = logging.getLogger("proyecta.experiencia")


def _inicio_del_dia() -> datetime:
    # Día en hora de Colombia (UTC-5): el tope diario se reinicia a medianoche local.
    ahora = utcnow() - timedelta(hours=5)
    return datetime.combine(ahora.date(), time(0), tzinfo=timezone.utc) + timedelta(hours=5)


def sumar(db: Session, usuario: Usuario | None, accion: str, referencia: str | None = None, detalle: str = "",
          tareas: BackgroundTasks | None = None, puntos: int | None = None, por: Usuario | None = None) -> int:
    """Suma la XP de una acción del catálogo. Devuelve los puntos sumados (0 si no aplica).

    Con `puntos` se usa ese valor en lugar del de la acción (evidencias y ajustes del admin).
    Quien llama hace commit.
    """
    if usuario is None or not usuario.activo:
        return 0
    if puntos is None:
        definicion = db.get(AccionXP, accion)
        if definicion is None or not definicion.activo or definicion.puntos == 0:
            return 0
        if definicion.tope_diario:
            hoy = db.scalar(select(func.count(MovimientoXP.id)).where(
                MovimientoXP.usuario_id == usuario.id, MovimientoXP.accion == accion,
                MovimientoXP.creado_en >= _inicio_del_dia())) or 0
            if hoy >= definicion.tope_diario:
                return 0
        puntos = definicion.puntos
        detalle = detalle or definicion.nombre
    if referencia is not None and db.scalar(select(MovimientoXP.id).where(
            MovimientoXP.usuario_id == usuario.id, MovimientoXP.accion == accion, MovimientoXP.referencia == referencia)):
        return 0
    db.add(MovimientoXP(usuario_id=usuario.id, accion=accion, puntos=puntos, detalle=detalle[:500], referencia=referencia,
                        otorgado_por_id=por.id if por else None))
    usuario.xp = max(0, (usuario.xp or 0) + puntos)
    db.flush()
    recalcular_nivel(db, usuario, tareas)
    return puntos


def sumar_a_varios(db: Session, ids, accion: str, referencia: str | None, detalle: str = "",
                   tareas: BackgroundTasks | None = None) -> None:
    for uid in {i for i in ids if i}:
        sumar(db, db.get(Usuario, uid), accion, referencia, detalle, tareas)


# ---- Niveles ---------------------------------------------------------------------------------

def niveles_ordenados(db: Session) -> list[Nivel]:
    return list(db.scalars(select(Nivel).order_by(Nivel.xp_minima, Nivel.insignias_minimas, Nivel.id)))


def _insignias_de(db: Session, usuario: Usuario) -> set[int]:
    from app.modules.insignias.servicio import vigentes
    return {f.insignia_id for f in vigentes(db, [usuario.id]).get(usuario.id, [])}


def cumple_nivel(nivel: Nivel, xp: int, insignias: set[int]) -> bool:
    return (xp >= nivel.xp_minima and len(insignias) >= nivel.insignias_minimas
            and all(i in insignias for i in (nivel.insignias_requeridas or [])))


@dataclass
class EstadoNivel:
    actual: Nivel | None
    siguiente: Nivel | None
    posicion: int  # 1 = primer nivel
    total: int
    insignias: set[int]


def estado(db: Session, usuario: Usuario, niveles: list[Nivel] | None = None, insignias: set[int] | None = None) -> EstadoNivel:
    """Los niveles se suben en orden: el actual es el último cumplido sin saltarse ninguno."""
    niveles = niveles if niveles is not None else niveles_ordenados(db)
    insignias = insignias if insignias is not None else _insignias_de(db, usuario)
    actual, k = None, 0
    for k, nivel in enumerate(niveles):
        if not cumple_nivel(nivel, usuario.xp or 0, insignias):
            return EstadoNivel(actual, nivel, k, len(niveles), insignias)
        actual = nivel
    return EstadoNivel(actual, None, len(niveles), len(niveles), insignias)


def recalcular_nivel(db: Session, usuario: Usuario, tareas: BackgroundTasks | None = None) -> bool:
    """Actualiza el nivel guardado. Si subió, avisa (campana + correo). Devuelve True si subió."""
    niveles = niveles_ordenados(db)
    nuevo = estado(db, usuario, niveles).actual
    anterior_id = usuario.nivel_id
    if (nuevo.id if nuevo else None) == anterior_id:
        return False
    usuario.nivel_id = nuevo.id if nuevo else None
    orden = {n.id: k for k, n in enumerate(niveles)}
    subio = nuevo is not None and (anterior_id is None or orden.get(nuevo.id, 0) > orden.get(anterior_id, -1))
    if subio and orden.get(nuevo.id, 0) > 0:  # llegar al primer nivel (Novato) no es noticia
        _avisar_subida(db, usuario, nuevo, tareas)
    return subio


def _avisar_subida(db: Session, usuario: Usuario, nivel: Nivel, tareas: BackgroundTasks | None) -> None:
    from app.modules.notificaciones.models import TipoNotificacion
    from app.modules.notificaciones.servicio import notificar

    notificar(db, usuario, TipoNotificacion.NIVEL, f"¡Subiste a nivel {nivel.nombre}!",
              nivel.descripcion or f"Ya tienes {usuario.xp} puntos de experiencia.", "/perfil#nivel", tareas,
              asunto=f"Subiste de nivel en Proyecta: {nivel.nombre}",
              parrafos=[f"Ahora eres {nivel.nombre}. {nivel.descripcion}".strip(), f"Experiencia acumulada: {usuario.xp} XP."],
              boton="Ver mi nivel")


def recalcular_todos(db: Session) -> int:
    """Tras editar los niveles: actualiza el nivel de todos (sin avisar a quienes bajan)."""
    n = 0
    for u in db.scalars(select(Usuario)).unique().all():
        if recalcular_nivel(db, u):
            n += 1
    db.commit()
    return n


def recalcular_xp(db: Session, usuario: Usuario) -> None:
    """La XP guardada siempre es la suma del historial (por si algo quedó desfasado)."""
    usuario.xp = max(0, db.scalar(select(func.coalesce(func.sum(MovimientoXP.puntos), 0))
                                  .where(MovimientoXP.usuario_id == usuario.id)) or 0)


def tarea_periodica_ingreso(db: Session, usuario: Usuario) -> None:
    """XP por entrar a la plataforma (una vez al día)."""
    hoy = (utcnow() - timedelta(hours=5)).date().isoformat()
    if sumar(db, usuario, "ingreso_diario", referencia=hoy):
        db.commit()
