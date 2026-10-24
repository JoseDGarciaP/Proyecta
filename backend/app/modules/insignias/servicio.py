"""Reglas de las insignias (uno o varios requisitos) y entrega con aviso en la campana y por correo."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from fastapi import BackgroundTasks
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.modules.insignias.models import Insignia, UsuarioInsignia
from app.modules.usuarios.models import Usuario

# Deben coincidir con ICONOS en src/components/Insignia.tsx.
ICONOS = [
    "award", "trophy", "medal", "star", "crown", "gem", "ribbon", "badge_check", "shield", "shield_check",
    "rocket", "lightbulb", "sparkles", "zap", "flame", "target", "goal", "flag", "mountain", "compass",
    "handshake", "users", "heart", "hand_heart", "smile", "thumbs_up", "megaphone", "message", "gift", "infinity",
    "graduation", "school", "book", "book_check", "brain", "microscope", "flask", "atom", "dna", "telescope",
    "code", "cpu", "laptop", "chart", "calculator", "palette", "pen", "camera", "mic", "music",
    "leaf", "sprout", "tree", "recycle", "droplets", "sun", "wind", "wheat", "tractor", "globe",
    "briefcase", "building", "landmark", "scale", "stethoscope", "hammer", "wrench", "puzzle", "key", "clock",
    "calendar_check", "hourglass", "map", "anchor", "feather", "dumbbell", "bike", "footprints", "eye", "glasses",
]
COLORES = ["brand", "accent", "amber", "orange", "rose", "fuchsia", "violet", "indigo", "sky", "teal", "emerald", "lime", "slate"]


# ---- Criterios -------------------------------------------------------------------------------

def _proyectos_de(db: Session, u: Usuario):
    """Proyectos donde participa (registrados por la persona o donde es miembro)."""
    from app.modules.alianzas.models import Miembro
    from app.modules.proyectos.models import Proyecto
    miembro = select(Miembro.proyecto_id).where(Miembro.usuario_id == u.id)
    return or_(Proyecto.creado_por_id == u.id, Proyecto.id.in_(miembro))


def _proyectos_registrados(db, u, _):
    from app.modules.proyectos.models import Proyecto
    return db.scalar(select(func.count(Proyecto.id)).where(Proyecto.creado_por_id == u.id)) or 0


def _colaboraciones(db, u, _):
    from app.modules.alianzas.models import Miembro
    return db.scalar(select(func.count()).where(Miembro.usuario_id == u.id)) or 0


def _integrantes_sumados(db, u, _):
    from app.modules.alianzas.models import Miembro
    from app.modules.proyectos.models import Proyecto
    return db.scalar(select(func.count()).select_from(Miembro).join(Proyecto, Proyecto.id == Miembro.proyecto_id)
                     .where(Proyecto.creado_por_id == u.id)) or 0


def _proyectos_finalizados(db, u, _):
    from app.modules.proyectos.models import Estado, Proyecto
    return db.scalar(select(func.count(Proyecto.id)).where(Proyecto.estado == Estado.FINALIZADO, _proyectos_de(db, u))) or 0


def _proyectos_en_area(db, u, valor):
    from app.modules.catalogo.models import Area
    from app.modules.proyectos.models import Proyecto
    return db.scalar(select(func.count(Proyecto.id)).join(Area, Area.id == Proyecto.area_id)
                     .where(Area.nombre == valor, _proyectos_de(db, u))) or 0


def _proyectos_con_ods(db, u, valor):
    from app.modules.catalogo.models import Ods
    from app.modules.proyectos.models import Proyecto
    try:
        ods = int(valor)
    except (TypeError, ValueError):
        return 0
    return db.scalar(select(func.count(Proyecto.id)).where(Proyecto.ods.any(Ods.id == ods), _proyectos_de(db, u))) or 0


def _solicitudes_aprobadas(db, u, _):
    from app.modules.alianzas.models import EstadoSolicitud, Solicitud, TipoSolicitud
    return db.scalar(select(func.count(Solicitud.id)).where(
        Solicitud.usuario_id == u.id, Solicitud.tipo == TipoSolicitud.SOLICITUD, Solicitud.estado == EstadoSolicitud.ACEPTADA)) or 0


def _invitaciones_aceptadas(db, u, _):
    from app.modules.alianzas.models import EstadoSolicitud, Solicitud, TipoSolicitud
    from app.modules.proyectos.models import Proyecto
    return db.scalar(select(func.count(Solicitud.id)).join(Proyecto, Proyecto.id == Solicitud.proyecto_id).where(
        Proyecto.creado_por_id == u.id, Solicitud.tipo == TipoSolicitud.INVITACION, Solicitud.estado == EstadoSolicitud.ACEPTADA)) or 0


def _horas_comprometidas(db, u, _):
    """Suma de horas por semana de sus colaboraciones aprobadas."""
    from app.modules.alianzas.models import EstadoSolicitud, Solicitud
    return db.scalar(select(func.coalesce(func.sum(Solicitud.disponibilidad_horas), 0)).where(
        Solicitud.usuario_id == u.id, Solicitud.estado == EstadoSolicitud.ACEPTADA)) or 0


def _perfil_completo(db, u, _):
    return int(bool((u.bio or "").strip() and u.habilidades and u.intereses))


def _habilidades(db, u, _):
    return len(u.habilidades or [])


def _mensajes_enviados(db, u, _):
    from app.modules.chat.models import Mensaje
    return db.scalar(select(func.count(Mensaje.id)).where(Mensaje.autor_id == u.id, Mensaje.eliminado.is_(False))) or 0


def _dias_en_plataforma(db, u, _):
    return (date.today() - u.creado_en).days if u.creado_en else 0


def _es_rol(db, u, valor):
    return int(u.rol == valor)


def _programa(db, u, valor):
    return int(bool(valor) and (valor or "").strip().lower() in (u.programa or "").lower())


def _xp_total(db, u, _):
    return u.xp or 0


def _nivel_alcanzado(db, u, _):
    from app.modules.experiencia.servicio import niveles_ordenados
    return next((k for k, n in enumerate(niveles_ordenados(db), start=1) if n.id == u.nivel_id), 0)


def _postulaciones(db, u, _, aceptadas: bool = False):
    from app.modules.postulaciones.models import EstadoPostulacion, Postulacion
    from app.modules.proyectos.models import Proyecto
    stmt = select(func.count(Postulacion.id)).join(Proyecto, Proyecto.id == Postulacion.proyecto_id).where(_proyectos_de(db, u))
    stmt = stmt.where(Postulacion.estado == EstadoPostulacion.ACEPTADA) if aceptadas else stmt.where(Postulacion.estado != EstadoPostulacion.RETIRADA)
    return db.scalar(stmt) or 0


def _evidencias_aprobadas(db, u, _):
    from app.modules.evidencias.models import EstadoEvidencia, Evidencia
    return db.scalar(select(func.count(Evidencia.id)).where(Evidencia.usuario_id == u.id, Evidencia.estado == EstadoEvidencia.APROBADA)) or 0


def _insignias_obtenidas(db, u, _):
    return len(vigentes(db, [u.id]).get(u.id, []))


@dataclass(frozen=True)
class Criterio:
    nombre: str
    unidad: str
    contar: Callable
    valor: str | None = None  # qué pide además del número: area | ods | rol | texto
    binario: bool = False  # se cumple o no (sin umbral)
    grupo: str = "Participación"


CRITERIOS: dict[str, Criterio] = {
    "proyectos_registrados": Criterio("Proyectos registrados", "proyectos", _proyectos_registrados, grupo="Proyectos"),
    "proyectos_finalizados": Criterio("Proyectos finalizados en los que participa", "proyectos", _proyectos_finalizados, grupo="Proyectos"),
    "proyectos_en_area": Criterio("Proyectos en un área", "proyectos", _proyectos_en_area, valor="area", grupo="Proyectos"),
    "proyectos_con_ods": Criterio("Proyectos con un ODS", "proyectos", _proyectos_con_ods, valor="ods", grupo="Proyectos"),
    "colaboraciones": Criterio("Proyectos de otros donde colabora", "proyectos", _colaboraciones, grupo="Colaboración"),
    "solicitudes_aprobadas": Criterio("Solicitudes para unirse aprobadas", "solicitudes", _solicitudes_aprobadas, grupo="Colaboración"),
    "integrantes_sumados": Criterio("Personas sumadas a sus proyectos", "personas", _integrantes_sumados, grupo="Colaboración"),
    "invitaciones_aceptadas": Criterio("Invitaciones suyas aceptadas", "invitaciones", _invitaciones_aceptadas, grupo="Colaboración"),
    "horas_comprometidas": Criterio("Horas por semana en colaboraciones aprobadas", "horas", _horas_comprometidas, grupo="Colaboración"),
    "mensajes_enviados": Criterio("Mensajes enviados en chats de equipo", "mensajes", _mensajes_enviados, grupo="Colaboración"),
    "perfil_completo": Criterio("Perfil completo", "", _perfil_completo, binario=True, grupo="Perfil"),
    "habilidades": Criterio("Habilidades en su perfil", "habilidades", _habilidades, grupo="Perfil"),
    "dias_en_plataforma": Criterio("Antigüedad de la cuenta", "días", _dias_en_plataforma, grupo="Perfil"),
    "es_rol": Criterio("Tiene el rol", "", _es_rol, valor="rol", binario=True, grupo="Perfil"),
    "programa": Criterio("Su programa o dependencia contiene", "", _programa, valor="texto", binario=True, grupo="Perfil"),
    "insignias_obtenidas": Criterio("Insignias vigentes (de otras)", "insignias", _insignias_obtenidas, grupo="Perfil"),
    "xp_total": Criterio("Experiencia acumulada", "XP", _xp_total, grupo="Experiencia"),
    "nivel_alcanzado": Criterio("Nivel alcanzado (posición: 1 = primero)", "", _nivel_alcanzado, grupo="Experiencia"),
    "postulaciones_enviadas": Criterio("Postulaciones a oportunidades", "postulaciones", _postulaciones, grupo="Oportunidades"),
    "postulaciones_aceptadas": Criterio("Postulaciones seleccionadas", "postulaciones",
                                        lambda db, u, v: _postulaciones(db, u, v, aceptadas=True), grupo="Oportunidades"),
    "evidencias_aprobadas": Criterio("Certificados o evidencias aprobadas", "evidencias", _evidencias_aprobadas, grupo="Experiencia"),
}


def texto_condicion(db: Session, c: dict) -> str:
    criterio = CRITERIOS.get(c.get("criterio", ""))
    if criterio is None:
        return c.get("criterio", "")
    valor = c.get("valor")
    if criterio.valor == "rol":
        from app.modules.roles.servicio import nombre_rol
        valor = nombre_rol(db, valor or "")
    elif criterio.valor == "ods":
        valor = f"ODS {valor}"
    if criterio.binario:
        return f"{criterio.nombre} «{valor}»" if valor else criterio.nombre
    detalle = f" «{valor}»" if valor else ""
    return f"{criterio.nombre}{detalle}: {c.get('umbral', 1)} o más"


def texto_regla(db: Session, insignia: Insignia) -> str:
    if not insignia.automatica:
        return "La otorga la administración"
    union = " y " if insignia.modo == "todas" else " o "
    return union.join(texto_condicion(db, c) for c in insignia.condiciones)


def progreso(db: Session, usuario: Usuario, insignia: Insignia, cache: dict | None = None) -> list[tuple[dict, int]]:
    """[(condición, valor actual)] de cada requisito."""
    cache = {} if cache is None else cache
    salida = []
    for c in insignia.condiciones:
        criterio = CRITERIOS.get(c.get("criterio", ""))
        clave = (c.get("criterio"), c.get("valor"))
        if clave not in cache:
            cache[clave] = criterio.contar(db, usuario, c.get("valor")) if criterio else 0
        salida.append((c, cache[clave]))
    return salida


def cumple(db: Session, usuario: Usuario, insignia: Insignia, cache: dict | None = None) -> bool:
    if not insignia.automatica:
        return False
    resultados = [actual >= (c.get("umbral") or 1) for c, actual in progreso(db, usuario, insignia, cache)]
    return all(resultados) if insignia.modo == "todas" else any(resultados)


# ---- Entrega ---------------------------------------------------------------------------------

def _fin_del_dia(d: date) -> datetime:
    return datetime.combine(d, time(23, 59, 59), tzinfo=timezone.utc)


def calcular_vencimiento(insignia: Insignia, desde: datetime, override: date | None = None) -> datetime | None:
    if override:
        return _fin_del_dia(override)
    opciones = []
    if insignia.vence_en:
        opciones.append(_fin_del_dia(insignia.vence_en))
    if insignia.vigencia_dias:
        opciones.append(desde + timedelta(days=insignia.vigencia_dias))
    return min(opciones) if opciones else None


def avisar(db: Session, usuario: Usuario, insignia: Insignia, motivo: str, tareas: BackgroundTasks | None) -> None:
    from app.modules.insignias.models import TIPOS
    from app.modules.notificaciones.models import TipoNotificacion
    from app.modules.notificaciones.servicio import notificar

    clase = TIPOS.get(insignia.tipo, "Insignia")
    verbo = "Recibiste la condecoración" if insignia.tipo == "condecoracion" else "¡Ganaste la insignia" if insignia.tipo == "logro" else "Recibiste el reconocimiento"
    titulo = f"{verbo} «{insignia.nombre}»" + ("!" if insignia.tipo == "logro" else "")
    parrafos = [insignia.descripcion] if insignia.descripcion else []
    if motivo and motivo != insignia.descripcion:
        parrafos.append(f"Motivo: {motivo}")
    if insignia.entidad:
        parrafos.append(f"Otorgada en nombre de: {insignia.entidad}")
    notificar(db, usuario, TipoNotificacion.INSIGNIA, titulo, motivo or insignia.descripcion, "/perfil#logros", tareas,
              asunto=f"{clase} en Proyecta: {insignia.nombre}", parrafos=parrafos, boton="Ver mis logros")


def otorgar(db: Session, usuario: Usuario, insignia: Insignia, motivo: str, por: Usuario | None,
            tareas: BackgroundTasks | None = None, fecha_evento: date | None = None, vence: date | None = None) -> UsuarioInsignia:
    """Otorga (o vuelve a otorgar si se había retirado o vencido) y avisa. Quien llama hace commit."""
    fila = db.scalar(select(UsuarioInsignia).where(UsuarioInsignia.usuario_id == usuario.id,
                                                    UsuarioInsignia.insignia_id == insignia.id))
    if fila is None:
        fila = UsuarioInsignia(usuario_id=usuario.id, insignia_id=insignia.id)
        db.add(fila)
    ahora = utcnow()
    fila.insignia = insignia
    fila.motivo, fila.automatica = motivo, por is None
    fila.otorgada_por_id = por.id if por else None
    fila.otorgada_en, fila.retirada_en, fila.fecha_evento = ahora, None, fecha_evento
    fila.vence_en = calcular_vencimiento(insignia, ahora, vence)
    avisar(db, usuario, insignia, motivo, tareas)
    from app.modules.experiencia.servicio import sumar
    db.flush()
    sumar(db, usuario, "insignia_obtenida", str(insignia.id), f"Insignia «{insignia.nombre}»", tareas)
    return fila


def evaluar(db: Session, usuario: Usuario | None, tareas: BackgroundTasks | None = None) -> list[Insignia]:
    """Otorga las insignias automáticas que `usuario` ya cumple. No vuelve a dar las retiradas ni las vencidas."""
    if usuario is None or not usuario.activo:
        return []
    ya = set(db.scalars(select(UsuarioInsignia.insignia_id).where(UsuarioInsignia.usuario_id == usuario.id)))
    ganadas, cache = [], {}
    for insignia in db.scalars(select(Insignia).where(Insignia.activo.is_(True)).order_by(Insignia.orden)).all():
        if insignia.id in ya or not insignia.automatica:
            continue
        if cumple(db, usuario, insignia, cache):
            otorgar(db, usuario, insignia, insignia.descripcion, None, tareas)
            db.flush()  # para que «insignias obtenidas» cuente la recién otorgada
            cache.pop(("insignias_obtenidas", None), None)
            ganadas.append(insignia)
    return ganadas


def evaluar_ids(db: Session, ids, tareas: BackgroundTasks | None = None) -> int:
    n = 0
    for uid in {i for i in ids if i}:
        n += len(evaluar(db, db.get(Usuario, uid), tareas))
    return n


def evaluar_todos(db: Session) -> int:
    n = 0
    for usuario in db.scalars(select(Usuario).where(Usuario.activo.is_(True), Usuario.verificado.is_(True))).unique().all():
        n += len(evaluar(db, usuario))
    db.commit()
    return n


def tarea_periodica() -> None:
    """Para criterios que cambian solos (antigüedad, rol): la API la corre cada cierto tiempo."""
    import logging

    from app.core.database import SessionLocal

    try:
        with SessionLocal() as db:
            evaluar_todos(db)
    except Exception:  # noqa: BLE001
        logging.getLogger("proyecta.insignias").exception("No se pudo revisar las insignias")


def vigente_ahora():
    ahora = utcnow()
    return (UsuarioInsignia.retirada_en.is_(None)) & (or_(UsuarioInsignia.vence_en.is_(None), UsuarioInsignia.vence_en > ahora))


def vigentes(db: Session, usuario_ids) -> dict:
    """Insignias vigentes (ni retiradas ni vencidas) de varias personas: {usuario_id: [UsuarioInsignia]}."""
    filas = db.scalars(
        select(UsuarioInsignia).join(Insignia)
        .where(UsuarioInsignia.usuario_id.in_(list(usuario_ids)), vigente_ahora(), Insignia.activo.is_(True))
        .order_by(Insignia.orden, UsuarioInsignia.otorgada_en)
    ).unique().all()
    salida: dict = {}
    for f in filas:
        salida.setdefault(f.usuario_id, []).append(f)
    return salida


def vencidas(db: Session, usuario_id) -> list[UsuarioInsignia]:
    ahora = utcnow()
    return list(db.scalars(
        select(UsuarioInsignia).join(Insignia)
        .where(UsuarioInsignia.usuario_id == usuario_id, UsuarioInsignia.retirada_en.is_(None),
               UsuarioInsignia.vence_en.is_not(None), UsuarioInsignia.vence_en <= ahora, Insignia.activo.is_(True))
        .order_by(UsuarioInsignia.vence_en.desc())
    ).unique())
