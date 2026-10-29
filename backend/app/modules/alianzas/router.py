import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.core.deps import DbSession, UsuarioActual, requiere
from app.modules.alianzas.models import EstadoSolicitud, Miembro, Solicitud, TipoSolicitud
from app.modules.alianzas.schemas import (
    Decision, MiembroSalida, NuevaInvitacion, NuevaSolicitud, Recomendacion, SolicitudSalida, envia, responde,
)
from app.modules.notificaciones.models import TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.parametros.models import Motivo, TipoAporte, TipoMotivo
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.router import obtener_proyecto
from app.modules.experiencia.servicio import sumar
from app.modules.insignias.servicio import evaluar_ids
from app.modules.roles.servicio import puede
from app.modules.usuarios.models import Usuario

router = APIRouter(tags=["alianzas"])


def es_miembro(db: Session, proyecto: Proyecto, usuario_id: uuid.UUID) -> bool:
    return proyecto.creado_por_id == usuario_id or db.get(Miembro, (proyecto.id, usuario_id)) is not None


def _validar_nueva(db: Session, proyecto: Proyecto, usuario_id: uuid.UUID) -> None:
    if es_miembro(db, proyecto, usuario_id):
        raise HTTPException(status_code=409, detail="Esa persona ya hace parte del proyecto")
    pendiente = db.scalar(select(Solicitud.id).where(
        Solicitud.proyecto_id == proyecto.id, Solicitud.usuario_id == usuario_id,
        Solicitud.estado == EstadoSolicitud.PENDIENTE,
    ))
    if pendiente:
        raise HTTPException(status_code=409, detail="Ya hay una solicitud pendiente para este proyecto")


def _nueva(db: Session, proyecto: Proyecto, usuario: Usuario, tipo: TipoSolicitud, datos: Recomendacion) -> Solicitud:
    aporte = db.get(TipoAporte, datos.tipo_aporte_id)
    if aporte is None or not aporte.activo:
        raise HTTPException(status_code=422, detail="Elige un tipo de aporte válido")
    solicitud = Solicitud(
        proyecto=proyecto, usuario=usuario, tipo=tipo, mensaje=datos.mensaje,
        tipo_aporte_id=aporte.id, rol_propuesto=aporte.nombre, aporte=datos.aporte, habilidades=datos.habilidades,
        disponibilidad_horas=datos.disponibilidad_horas, motivacion=datos.motivacion,
    )
    db.add(solicitud)
    return solicitud


def _detalles(s: Solicitud) -> list[tuple[str, str]]:
    filas = [("Proyecto", s.proyecto.titulo), ("Rol propuesto", s.rol_propuesto),
             ("Aporte" if s.tipo == TipoSolicitud.SOLICITUD else "Qué se espera", s.aporte),
             ("Disponibilidad", f"{s.disponibilidad_horas} horas por semana")]
    if s.habilidades:
        filas.append(("Habilidades", ", ".join(s.habilidades)))
    filas.append(("Motivación" if s.tipo == TipoSolicitud.SOLICITUD else "Por qué te invitan", s.motivacion))
    if s.mensaje:
        filas.append(("Nota", s.mensaje))
    return filas


@router.post("/api/proyectos/{proyecto_id}/solicitudes", response_model=SolicitudSalida, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requiere("colaboracion.solicitar"))])
def solicitar_union(proyecto_id: uuid.UUID, datos: NuevaSolicitud, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    proyecto = obtener_proyecto(db, proyecto_id)
    if proyecto.creado_por_id is None:
        raise HTTPException(status_code=409, detail="El proyecto no tiene un responsable que pueda responder")
    _validar_nueva(db, proyecto, usuario.id)
    solicitud = _nueva(db, proyecto, usuario, TipoSolicitud.SOLICITUD, datos)
    db.flush()
    sumar(db, usuario, "solicitud_enviada", str(solicitud.id), f"Pidió unirse a «{proyecto.titulo}»", tareas)
    responsable = db.get(Usuario, proyecto.creado_por_id)
    if responsable is not None:
        notificar(
            db, responsable, TipoNotificacion.SOLICITUD_NUEVA,
            f"{usuario.nombre} quiere unirse a «{proyecto.titulo}»",
            f"Propone aportar como {solicitud.rol_propuesto}, {solicitud.disponibilidad_horas} h por semana.",
            f"/perfil#solicitud-{solicitud.id}", tareas,
            asunto=f"Nueva solicitud para «{proyecto.titulo}»",
            parrafos=[f"{usuario.nombre} pidió unirse a tu proyecto. Esta es su propuesta:"],
            detalles=_detalles(solicitud), boton="Revisar la solicitud",
        )
    db.commit()
    return SolicitudSalida.de(solicitud, usuario.id)


@router.post("/api/proyectos/{proyecto_id}/invitaciones", response_model=SolicitudSalida, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requiere("colaboracion.invitar"))])
def invitar(proyecto_id: uuid.UUID, datos: NuevaInvitacion, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    proyecto = obtener_proyecto(db, proyecto_id)
    if proyecto.creado_por_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto puede invitar")
    invitado = db.get(Usuario, datos.usuario_id)
    if invitado is None or not invitado.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    solicitud = invitar_usuario(db, proyecto, usuario, invitado, datos, tareas)
    return SolicitudSalida.de(solicitud, usuario.id)


def invitar_usuario(db: Session, proyecto: Proyecto, usuario: Usuario, invitado: Usuario, datos: Recomendacion,
                    tareas: BackgroundTasks) -> Solicitud:
    """Crea la invitación para alguien que ya tiene cuenta y le avisa (campana y correo)."""
    _validar_nueva(db, proyecto, invitado.id)
    solicitud = _nueva(db, proyecto, invitado, TipoSolicitud.INVITACION, datos)
    db.flush()
    sumar(db, usuario, "invitacion_enviada", str(solicitud.id), f"Invitó a {invitado.nombre} a «{proyecto.titulo}»", tareas)
    notificar(
        db, invitado, TipoNotificacion.INVITACION_NUEVA,
        f"{usuario.nombre} te invitó a «{proyecto.titulo}»",
        f"Te propone participar como {solicitud.rol_propuesto}, {solicitud.disponibilidad_horas} h por semana.",
        f"/perfil#solicitud-{solicitud.id}", tareas,
        asunto=f"Te invitaron al proyecto «{proyecto.titulo}»",
        parrafos=[f"{usuario.nombre}, responsable del proyecto, te invitó a colaborar. Esta es la propuesta:"],
        detalles=_detalles(solicitud), boton="Ver la invitación",
    )
    db.commit()
    return solicitud


@router.get("/api/proyectos/{proyecto_id}/miembros", response_model=list[MiembroSalida])
def listar_miembros(proyecto_id: uuid.UUID, db: DbSession):
    obtener_proyecto(db, proyecto_id)
    miembros = db.scalars(select(Miembro).where(Miembro.proyecto_id == proyecto_id).order_by(Miembro.desde))
    return [MiembroSalida.de(m) for m in miembros]


@router.delete("/api/proyectos/{proyecto_id}/miembros/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def retirar_miembro(proyecto_id: uuid.UUID, usuario_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """Quien registró el proyecto (o un admin) retira a alguien; un miembro puede retirarse a sí mismo."""
    proyecto = obtener_proyecto(db, proyecto_id)
    if usuario.id not in (usuario_id, proyecto.creado_por_id) and not puede(db, usuario, "proyectos.moderar"):
        raise HTTPException(status_code=403, detail="No puedes retirar a este miembro")
    miembro = db.get(Miembro, (proyecto_id, usuario_id))
    if miembro is None:
        raise HTTPException(status_code=404, detail="No es miembro del proyecto")
    db.delete(miembro)
    db.commit()


def solicitudes_de(db: Session, usuario_id: uuid.UUID) -> list[Solicitud]:
    """Las que envié, las que me enviaron y las de los proyectos que registré."""
    stmt = (
        select(Solicitud).join(Solicitud.proyecto)
        .where(or_(Solicitud.usuario_id == usuario_id, Proyecto.creado_por_id == usuario_id))
        .order_by(Solicitud.creado_en.desc(), Solicitud.actualizado_en.desc())
    )
    return list(db.scalars(stmt).unique())


@router.get("/api/alianzas", response_model=list[SolicitudSalida])
def mis_solicitudes(usuario: UsuarioActual, db: DbSession, estado: EstadoSolicitud | None = None):
    return [SolicitudSalida.de(s, usuario.id) for s in solicitudes_de(db, usuario.id) if estado in (None, s.estado)]


def _obtener(db: Session, solicitud_id: uuid.UUID) -> Solicitud:
    solicitud = db.get(Solicitud, solicitud_id)
    if solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise HTTPException(status_code=409, detail=f"La solicitud ya fue {solicitud.estado.value}")
    return solicitud


def _motivo(db: Session, decision: Decision, estado: EstadoSolicitud) -> Motivo:
    tipo = TipoMotivo.APROBACION if estado == EstadoSolicitud.ACEPTADA else TipoMotivo.RECHAZO
    motivo = db.get(Motivo, decision.motivo_id)
    if motivo is None or not motivo.activo or motivo.tipo != tipo:
        accion = "aprobar" if tipo == TipoMotivo.APROBACION else "rechazar"
        raise HTTPException(status_code=422, detail=f"Elige un motivo válido para {accion}")
    if motivo.requiere_comentario and not decision.respuesta.strip():
        raise HTTPException(status_code=422, detail=f"El motivo «{motivo.nombre}» requiere un comentario")
    return motivo


def _avisar_cierre(db: Session, s: Solicitud, quien: Usuario, tareas: BackgroundTasks) -> None:
    """Avisa a la otra parte que la solicitud o invitación se decidió o se canceló."""
    destino_id = responde(s) if s.estado == EstadoSolicitud.CANCELADA else envia(s)
    destino = db.get(Usuario, destino_id) if destino_id else None
    if destino is None or destino.id == quien.id:
        return
    clase = "solicitud" if s.tipo == TipoSolicitud.SOLICITUD else "invitación"
    proyecto = s.proyecto.titulo
    detalles = [("Proyecto", proyecto)]
    if s.estado == EstadoSolicitud.CANCELADA:
        tipo, titulo = TipoNotificacion.SOLICITUD_CANCELADA, f"{quien.nombre} retiró la {clase} de «{proyecto}»"
        cuerpo, enlace, boton = "Ya no tienes que responderla.", "/perfil", "Ir a mi perfil"
    else:
        aceptada = s.estado == EstadoSolicitud.ACEPTADA
        tipo = TipoNotificacion.SOLICITUD_ACEPTADA if aceptada else TipoNotificacion.SOLICITUD_RECHAZADA
        verbo = "aceptó" if aceptada else "rechazó"
        titulo = f"{quien.nombre} {verbo} tu {clase} de «{proyecto}»"
        cuerpo = f"Motivo: {s.motivo_nombre}" + (f". Comentario: {s.respuesta}" if s.respuesta else "")
        detalles += [("Decisión", "Aprobada" if aceptada else "Rechazada"), ("Motivo", s.motivo_nombre)]
        if s.respuesta:
            detalles.append(("Comentario", s.respuesta))
        if aceptada:
            enlace, boton = f"/proyectos/{s.proyecto_id}", "Ir al proyecto"
        else:
            enlace, boton = f"/perfil#solicitud-{s.id}", "Ver el detalle"
    notificar(db, destino, tipo, titulo, cuerpo, enlace, tareas, detalles=detalles, boton=boton,
              parrafos=[cuerpo] if s.estado == EstadoSolicitud.CANCELADA else [])


def _cerrar(db: Session, solicitud: Solicitud, estado: EstadoSolicitud, quien: Usuario, tareas: BackgroundTasks,
            motivo: Motivo | None = None, respuesta: str = "") -> SolicitudSalida:
    solicitud.estado = estado
    solicitud.respuesta = respuesta.strip()
    solicitud.respondida_en = utcnow()
    if motivo is not None:
        solicitud.motivo_id, solicitud.motivo_nombre = motivo.id, motivo.nombre
    if estado == EstadoSolicitud.ACEPTADA and db.get(Miembro, (solicitud.proyecto_id, solicitud.usuario_id)) is None:
        db.add(Miembro(proyecto_id=solicitud.proyecto_id, usuario_id=solicitud.usuario_id,
                       rol=(solicitud.rol_propuesto or "colaborador")[:80]))
    _avisar_cierre(db, solicitud, quien, tareas)
    if estado == EstadoSolicitud.ACEPTADA:
        db.flush()
        titulo = solicitud.proyecto.titulo
        sumar(db, solicitud.usuario, "colaboracion_aprobada", str(solicitud.id), f"Entró al equipo de «{titulo}»", tareas)
        responsable = db.get(Usuario, solicitud.proyecto.creado_por_id) if solicitud.proyecto.creado_por_id else None
        sumar(db, responsable, "integrante_sumado", str(solicitud.id), f"{solicitud.usuario.nombre} se sumó a «{titulo}»", tareas)
        # «Colaborador/a» para quien entra, «Líder de equipo» para el responsable.
        evaluar_ids(db, [solicitud.usuario_id, solicitud.proyecto.creado_por_id], tareas)
    db.commit()
    return SolicitudSalida.de(solicitud, quien.id)


def _decidir(solicitud_id: uuid.UUID, datos: Decision, usuario: Usuario, db: Session, estado: EstadoSolicitud,
             tareas: BackgroundTasks):
    solicitud = _obtener(db, solicitud_id)
    if responde(solicitud) != usuario.id:
        raise HTTPException(status_code=403, detail="Esta solicitud la responde otra persona")
    motivo = _motivo(db, datos, estado)
    return _cerrar(db, solicitud, estado, usuario, tareas, motivo, datos.respuesta)


@router.post("/api/alianzas/{solicitud_id}/aceptar", response_model=SolicitudSalida)
def aceptar(solicitud_id: uuid.UUID, datos: Decision, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    return _decidir(solicitud_id, datos, usuario, db, EstadoSolicitud.ACEPTADA, tareas)


@router.post("/api/alianzas/{solicitud_id}/rechazar", response_model=SolicitudSalida)
def rechazar(solicitud_id: uuid.UUID, datos: Decision, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    return _decidir(solicitud_id, datos, usuario, db, EstadoSolicitud.RECHAZADA, tareas)


@router.post("/api/alianzas/{solicitud_id}/cancelar", response_model=SolicitudSalida)
def cancelar(solicitud_id: uuid.UUID, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    """Quien envió la solicitud o la invitación la retira antes de que respondan."""
    solicitud = _obtener(db, solicitud_id)
    if responde(solicitud) == usuario.id or usuario.id not in (solicitud.usuario_id, solicitud.proyecto.creado_por_id):
        raise HTTPException(status_code=403, detail="Solo quien la envió puede cancelarla")
    return _cerrar(db, solicitud, EstadoSolicitud.CANCELADA, usuario, tareas)
