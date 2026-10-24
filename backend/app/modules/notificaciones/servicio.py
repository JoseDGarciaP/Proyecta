"""Crear avisos: una fila en la campana y, si la persona y el admin lo permiten, un correo."""

import logging
from datetime import datetime, timedelta

from fastapi import BackgroundTasks
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core import correo
from app.core.config import get_settings
from app.core.database import SessionLocal, utcnow
from app.modules.notificaciones.models import CATEGORIA, Notificacion, TipoNotificacion
from app.modules.parametros import ajustes as ajustes_srv
from app.modules.usuarios.models import Usuario

log = logging.getLogger("proyecta.notificaciones")


def url(ruta: str) -> str:
    return f"{get_settings().frontend_url.rstrip('/')}{ruta}"


def notificar(
    db: Session,
    usuario: Usuario,
    tipo: TipoNotificacion,
    titulo: str,
    cuerpo: str,
    enlace: str,
    tareas: BackgroundTasks | None = None,
    *,
    asunto: str | None = None,
    parrafos: list[str] | None = None,
    detalles: list[tuple[str, str]] | None = None,
    boton: str = "Abrir en Proyecta",
) -> Notificacion:
    """Agrega el aviso a la sesión (quien llama hace commit) y programa el correo si corresponde.

    Con `tareas` el correo sale después de responder; sin ellas se envía en el momento.
    """
    categoria = CATEGORIA[tipo]
    aviso = Notificacion(usuario_id=usuario.id, tipo=tipo, titulo=titulo, cuerpo=cuerpo, enlace=enlace)
    db.add(aviso)
    permitido = getattr(ajustes_srv.leer(db), f"correo_{categoria}")
    if permitido and usuario.activo and (categoria == "cuenta" or usuario.quiere_correo(categoria)):
        mensaje = correo.alerta(
            para=usuario.email, nombre=usuario.nombre, asunto=asunto or f"Proyecta: {titulo}", titulo=titulo,
            parrafos=parrafos if parrafos is not None else ([cuerpo] if cuerpo else []),
            enlace=url(enlace), boton=boton, detalles=detalles, apagable=categoria != "cuenta",
        )
        if tareas is not None:
            tareas.add_task(correo.enviar, mensaje)
        else:
            correo.enviar(mensaje)
        aviso.correo_enviado = True
    return aviso


# ---- Resumen de mensajes sin leer ------------------------------------------------------------

def _sin_leer(db: Session, usuario: Usuario, desde: datetime, hasta: datetime) -> list[tuple[str, str, int]]:
    """(título del chat, enlace, cantidad) de los mensajes de otros sin leer enviados entre `desde` y `hasta`."""
    from app.modules.alianzas.models import Miembro, Solicitud
    from app.modules.chat.models import Lectura, LecturaSolicitud, Mensaje, MensajeSolicitud
    from app.modules.proyectos.models import Proyecto

    chats: list[tuple[str, str, int]] = []
    leido = func.coalesce(Lectura.ultimo_leido_id, 0)
    filas = db.execute(
        select(Proyecto.id, Proyecto.titulo, func.count(Mensaje.id))
        .join(Mensaje, Mensaje.proyecto_id == Proyecto.id)
        .outerjoin(Miembro, (Miembro.proyecto_id == Proyecto.id) & (Miembro.usuario_id == usuario.id))
        .outerjoin(Lectura, (Lectura.proyecto_id == Proyecto.id) & (Lectura.usuario_id == usuario.id))
        .where(or_(Proyecto.creado_por_id == usuario.id, Miembro.usuario_id.is_not(None)))
        .where(Mensaje.id > leido, Mensaje.eliminado.is_(False))
        .where(or_(Mensaje.autor_id.is_(None), Mensaje.autor_id != usuario.id))
        .where(Mensaje.enviado_en > desde, Mensaje.enviado_en <= hasta)
        .group_by(Proyecto.id, Proyecto.titulo)
    ).all()
    chats += [(f"Equipo de «{titulo}»", f"/proyectos/{pid}#chat", n) for pid, titulo, n in filas]

    leido_s = func.coalesce(LecturaSolicitud.ultimo_leido_id, 0)
    filas = db.execute(
        select(Solicitud.id, Proyecto.titulo, func.count(MensajeSolicitud.id))
        .join(Proyecto, Proyecto.id == Solicitud.proyecto_id)
        .join(MensajeSolicitud, MensajeSolicitud.solicitud_id == Solicitud.id)
        .outerjoin(LecturaSolicitud, (LecturaSolicitud.solicitud_id == Solicitud.id) & (LecturaSolicitud.usuario_id == usuario.id))
        .where(or_(Solicitud.usuario_id == usuario.id, Proyecto.creado_por_id == usuario.id))
        .where(MensajeSolicitud.id > leido_s, MensajeSolicitud.eliminado.is_(False))
        .where(or_(MensajeSolicitud.autor_id.is_(None), MensajeSolicitud.autor_id != usuario.id))
        .where(MensajeSolicitud.enviado_en > desde, MensajeSolicitud.enviado_en <= hasta)
        .group_by(Solicitud.id, Proyecto.titulo)
    ).all()
    chats += [(f"Solicitud sobre «{titulo}»", f"/perfil#solicitud-{sid}", n) for sid, titulo, n in filas]
    return chats


def enviar_resumenes(db: Session, ahora: datetime | None = None) -> int:
    """Un solo aviso por persona con los mensajes que lleva sin leer más de `resumen_espera_minutos`.

    Cada mensaje se avisa una sola vez (se guarda hasta cuándo se avisó). Devuelve cuántos avisos se crearon.
    """
    ajustes = ajustes_srv.leer(db)
    ahora = ahora or utcnow()
    hasta = ahora - timedelta(minutes=ajustes.resumen_espera_minutos)
    enviados = 0
    usuarios = db.scalars(select(Usuario).where(Usuario.activo.is_(True), Usuario.verificado.is_(True))).all()
    for usuario in usuarios:
        # La primera vez solo se mira la última semana, para no avisar de conversaciones viejas.
        desde = usuario.resumen_hasta or (ahora - timedelta(days=7))
        if desde.tzinfo is None:  # SQLite devuelve fechas sin zona
            desde = desde.replace(tzinfo=hasta.tzinfo)
        if desde >= hasta:
            continue
        chats = _sin_leer(db, usuario, desde, hasta)
        usuario.resumen_hasta = hasta
        if not chats:
            continue
        total = sum(n for _, _, n in chats)
        plural = "mensaje" if total == 1 else "mensajes"
        titulo = f"Tienes {total} {plural} sin leer"
        enlace = chats[0][1] if len(chats) == 1 else "/perfil"
        notificar(
            db, usuario, TipoNotificacion.MENSAJES_SIN_LEER, titulo,
            ", ".join(f"{t} ({n})" for t, _, n in chats), enlace,
            parrafos=["Te escribieron en Proyecta y aún no lo has leído:"],
            detalles=[(t, f"{n} {'mensaje' if n == 1 else 'mensajes'}") for t, _, n in chats],
            boton="Leer mensajes",
        )
        enviados += 1
    db.commit()
    return enviados


def tarea_resumenes() -> None:
    """Para el ciclo periódico de la API y el script: abre su propia sesión."""
    try:
        with SessionLocal() as db:
            n = enviar_resumenes(db)
            if n:
                log.info("Resumen de mensajes sin leer enviado a %s personas", n)
    except Exception:  # noqa: BLE001 - el ciclo no debe morir por un error puntual
        log.exception("No se pudo enviar el resumen de mensajes sin leer")
