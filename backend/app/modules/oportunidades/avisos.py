"""Tareas diarias: avisos de convocatorias por cerrar (Ep6-Hu13) y archivo de notificaciones viejas (Ep6-Hu15)."""

import logging
import uuid
from datetime import date, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, utcnow
from app.modules.alianzas.models import Miembro
from app.modules.ia.models import EstadoRecomendacion, RecomendacionGuardada, TipoRecomendacion
from app.modules.notificaciones.models import Notificacion, TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.oportunidades.models import Oportunidad
from app.modules.postulaciones.models import EstadoPostulacion, Postulacion
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario

log = logging.getLogger("proyecta.avisos")
DIAS_ARCHIVO = 90


def _interesados(db: Session, op: Oportunidad) -> set[uuid.UUID]:
    """Equipos de proyectos a los que se les recomendó y aún no postulan, y personas con intereses en sus áreas."""
    ya_postularon = set(db.scalars(select(Postulacion.proyecto_id).where(
        Postulacion.oportunidad_id == op.id, Postulacion.estado != EstadoPostulacion.RETIRADA)))
    proyectos = set(db.scalars(select(RecomendacionGuardada.proyecto_id).where(
        RecomendacionGuardada.objetivo_id == op.id, RecomendacionGuardada.tipo == TipoRecomendacion.OPORTUNIDAD,
        RecomendacionGuardada.estado != EstadoRecomendacion.ANULADA))) - ya_postularon
    personas: set[uuid.UUID] = set()
    for p in db.scalars(select(Proyecto).where(Proyecto.id.in_(proyectos))).unique():
        if p.creado_por_id:
            personas.add(p.creado_por_id)
    personas.update(db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id.in_(proyectos))))
    areas = {a.nombre.lower() for a in op.areas}
    if areas:
        for u in db.scalars(select(Usuario).where(Usuario.activo.is_(True))):
            if areas & {i.lower() for i in (u.intereses or [])}:
                personas.add(u.id)
    return personas


def avisar_cierres(db: Session, hoy: date | None = None) -> int:
    """Avisa a 7 días y a 1 día del cierre, una sola vez cada uno. Devuelve cuántos avisos se crearon."""
    hoy = hoy or date.today()
    enviados = 0
    pendientes = db.scalars(select(Oportunidad).where(
        Oportunidad.archivada.is_(False), Oportunidad.cierra_en >= hoy, Oportunidad.cierra_en <= hoy + timedelta(days=7),
    )).unique()
    for op in pendientes:
        faltan = (op.cierra_en - hoy).days
        if faltan <= 1 and not op.aviso_1_dia:
            op.aviso_1_dia = op.aviso_7_dias = True
            cuando = "hoy" if faltan == 0 else "mañana"
        elif faltan <= 7 and not op.aviso_7_dias:
            op.aviso_7_dias = True
            cuando = f"en {faltan} días"
        else:
            continue
        for uid in _interesados(db, op):
            if (u := db.get(Usuario, uid)) is not None:
                notificar(db, u, TipoNotificacion.CONVOCATORIA, f"«{op.titulo}» cierra {cuando}",
                          f"{op.entidad} · cierra el {op.cierra_en.isoformat()}.", f"/oportunidades/{op.id}",
                          detalles=[("Entidad", op.entidad), ("Cierre", op.cierra_en.isoformat())], boton="Ver convocatoria")
                enviados += 1
    db.commit()
    return enviados


def archivar_notificaciones(db: Session, dias: int = DIAS_ARCHIVO) -> int:
    limite = utcnow() - timedelta(days=dias)
    res = db.execute(update(Notificacion).where(Notificacion.archivada.is_(False), Notificacion.creada_en < limite)
                     .values(archivada=True))
    db.commit()
    return res.rowcount or 0


def tarea_diaria() -> None:
    """Para el ciclo periódico de la API y el script: abre su propia sesión."""
    try:
        with SessionLocal() as db:
            n = avisar_cierres(db)
            m = archivar_notificaciones(db)
            if n or m:
                log.info("Avisos de cierre: %s · notificaciones archivadas: %s", n, m)
    except Exception:  # noqa: BLE001 - el ciclo no debe morir por un error puntual
        log.exception("No se pudo correr la tarea diaria")
