"""Invitaciones a un proyecto por correo, para personas que aún no tienen cuenta.

Flujo:
1. Quien registró el proyecto escribe un correo. Si ya hay una cuenta confirmada con ese correo, se
   crea una invitación normal (ver alianzas.router). Si no, se guarda una `InvitacionCorreo` y se
   envía un correo con un enlace de un solo uso.
2. Desde el enlace (página /invitacion) la persona ve la propuesta y la acepta o la rechaza sin
   necesidad de cuenta. Si acepta, la interfaz la lleva a crear la cuenta con ese correo.
3. Cuando una cuenta con ese correo queda confirmada (registro, enlace de verificación, Google o
   restablecer contraseña), `reclamar` convierte la invitación en una `Solicitud`: aceptada → entra
   al equipo de una vez; pendiente → le aparece en su perfil para responderla como cualquier otra.
"""

import hashlib
import secrets
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import correo
from app.core.config import get_settings
from app.core.database import utcnow
from app.core.deps import DbSession, UsuarioActual, requiere
from app.modules.alianzas.models import EstadoSolicitud, InvitacionCorreo, Solicitud, TipoSolicitud
from app.modules.alianzas.router import _cerrar, es_miembro, invitar_usuario
from app.modules.alianzas.schemas import Recomendacion, SolicitudSalida
from app.modules.experiencia.servicio import sumar
from app.modules.notificaciones.models import Notificacion, TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.parametros.models import TipoAporte
from app.modules.proyectos.router import obtener_proyecto
from app.modules.usuarios.models import Usuario

router = APIRouter(tags=["alianzas"])
publico = APIRouter(prefix="/api/invitaciones", tags=["invitaciones por correo"])

# Para que nadie use un proyecto como máquina de enviar correos.
MAX_PENDIENTES_POR_PROYECTO = 30
MOTIVO_ACEPTADA = "Aceptó la invitación enviada a su correo"


# ---- Esquemas ------------------------------------------------------------------------------------

class NuevaInvitacionCorreo(Recomendacion):
    email: str = Field(min_length=3, max_length=254)


class InvitacionCorreoSalida(BaseModel):
    id: uuid.UUID
    proyecto_id: uuid.UUID
    email: str
    estado: EstadoSolicitud
    rol_propuesto: str
    creado_en: date
    expira_en: datetime
    vencida: bool

    @classmethod
    def de(cls, i: InvitacionCorreo) -> "InvitacionCorreoSalida":
        return cls(id=i.id, proyecto_id=i.proyecto_id, email=i.email, estado=i.estado, rol_propuesto=i.rol_propuesto,
                   creado_en=i.creado_en, expira_en=i.expira_en, vencida=_vencida(i))


class ResultadoInvitarCorreo(BaseModel):
    # «usuario»: el correo ya tenía cuenta y se le envió una invitación normal.
    # «correo»: no tenía cuenta; se le envió el enlace para registrarse.
    modo: str
    solicitud: SolicitudSalida | None = None
    invitacion: InvitacionCorreoSalida | None = None


class InvitacionPublica(BaseModel):
    """Lo que ve quien abre el enlace del correo (no necesita sesión)."""

    email: str
    estado: EstadoSolicitud
    vencida: bool
    proyecto_id: uuid.UUID
    proyecto_titulo: str
    proyecto_resumen: str
    invitado_por: str
    rol_propuesto: str
    aporte: str
    habilidades: list[str]
    disponibilidad_horas: int | None
    motivacion: str
    mensaje: str
    # True si ya hay una cuenta confirmada con ese correo (solo tiene que ingresar).
    cuenta_existe: bool
    # True si la persona ya quedó en el equipo.
    es_miembro: bool


# ---- Utilidades ----------------------------------------------------------------------------------

def huella(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _aware(fecha: datetime) -> datetime:
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)  # SQLite devuelve fechas sin zona


def _vencida(i: InvitacionCorreo) -> bool:
    return i.estado == EstadoSolicitud.PENDIENTE and _aware(i.expira_en) < datetime.now(timezone.utc)


def _cuenta(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email))


def _detalles(i: InvitacionCorreo) -> list[tuple[str, str]]:
    filas = [("Proyecto", i.proyecto.titulo), ("Rol propuesto", i.rol_propuesto), ("Qué se espera", i.aporte),
             ("Disponibilidad", f"{i.disponibilidad_horas} horas por semana")]
    if i.habilidades:
        filas.append(("Habilidades", ", ".join(i.habilidades)))
    filas.append(("Por qué te invitan", i.motivacion))
    if i.mensaje:
        filas.append(("Nota", i.mensaje))
    return filas


def _por_token(db: Session, token: str) -> InvitacionCorreo:
    invitacion = db.scalar(select(InvitacionCorreo).where(InvitacionCorreo.token_hash == huella(token)))
    if invitacion is None:
        raise HTTPException(status_code=404, detail="La invitación no existe o el enlace está incompleto.")
    return invitacion


def _responsable(db: Session, proyecto_id: uuid.UUID, usuario: Usuario):
    proyecto = obtener_proyecto(db, proyecto_id)
    if proyecto.creado_por_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto puede invitar")
    return proyecto


# ---- Para quien registró el proyecto ------------------------------------------------------------

@router.post("/api/proyectos/{proyecto_id}/invitaciones-correo", response_model=ResultadoInvitarCorreo,
             status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere("colaboracion.invitar"))])
def invitar_por_correo(proyecto_id: uuid.UUID, datos: NuevaInvitacionCorreo, usuario: UsuarioActual, db: DbSession,
                       tareas: BackgroundTasks):
    from app.modules.auth.router import validar_correo

    proyecto = _responsable(db, proyecto_id, usuario)
    email = validar_correo(datos.email)
    recomendacion = Recomendacion.model_validate(datos.model_dump(exclude={"email"}))

    cuenta = _cuenta(db, email)
    if cuenta is not None and cuenta.verificado:
        if not cuenta.activo:
            raise HTTPException(status_code=409, detail="La cuenta con ese correo está desactivada")
        solicitud = invitar_usuario(db, proyecto, usuario, cuenta, recomendacion, tareas)
        return ResultadoInvitarCorreo(modo="usuario", solicitud=SolicitudSalida.de(solicitud, usuario.id))

    pendientes = db.scalars(select(InvitacionCorreo).where(
        InvitacionCorreo.proyecto_id == proyecto.id, InvitacionCorreo.estado == EstadoSolicitud.PENDIENTE,
        InvitacionCorreo.solicitud_id.is_(None),
    )).all()
    if any(i.email == email and not _vencida(i) for i in pendientes):
        raise HTTPException(status_code=409, detail="Ya enviaste una invitación a ese correo y sigue pendiente")
    if sum(not _vencida(i) for i in pendientes) >= MAX_PENDIENTES_POR_PROYECTO:
        raise HTTPException(status_code=429, detail="Hay demasiadas invitaciones por correo pendientes en este proyecto")
    # Una invitación vencida al mismo correo se reemplaza por la nueva.
    for vieja in pendientes:
        if vieja.email == email:
            vieja.estado = EstadoSolicitud.CANCELADA

    aporte = db.get(TipoAporte, recomendacion.tipo_aporte_id)
    if aporte is None or not aporte.activo:
        raise HTTPException(status_code=422, detail="Elige un tipo de aporte válido")
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    invitacion = InvitacionCorreo(
        proyecto=proyecto, email=email, invitado_por_id=usuario.id, token_hash=huella(token),
        expira_en=utcnow() + timedelta(days=settings.invitacion_dias),
        tipo_aporte_id=aporte.id, rol_propuesto=aporte.nombre, aporte=recomendacion.aporte,
        habilidades=recomendacion.habilidades, disponibilidad_horas=recomendacion.disponibilidad_horas,
        motivacion=recomendacion.motivacion, mensaje=recomendacion.mensaje,
    )
    db.add(invitacion)
    db.flush()
    sumar(db, usuario, "invitacion_enviada", str(invitacion.id), f"Invitó a {email} a «{proyecto.titulo}»", tareas)
    enlace = f"{settings.frontend_url.rstrip('/')}/invitacion?token={token}"
    tareas.add_task(correo.enviar, correo.invitacion_proyecto(
        email, usuario.nombre, proyecto.titulo, _detalles(invitacion), enlace, settings.invitacion_dias))
    db.commit()
    return ResultadoInvitarCorreo(modo="correo", invitacion=InvitacionCorreoSalida.de(invitacion))


@router.get("/api/proyectos/{proyecto_id}/invitaciones-correo", response_model=list[InvitacionCorreoSalida])
def listar_invitaciones_correo(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    """Las invitaciones por correo que aún esperan respuesta o registro (solo para el responsable)."""
    _responsable(db, proyecto_id, usuario)
    filas = db.scalars(select(InvitacionCorreo).where(
        InvitacionCorreo.proyecto_id == proyecto_id, InvitacionCorreo.solicitud_id.is_(None),
        InvitacionCorreo.estado.in_([EstadoSolicitud.PENDIENTE, EstadoSolicitud.ACEPTADA]),
    ).order_by(InvitacionCorreo.creado_en.desc(), InvitacionCorreo.actualizado_en.desc()))
    return [InvitacionCorreoSalida.de(i) for i in filas]


@router.post("/api/invitaciones-correo/{invitacion_id}/cancelar", response_model=InvitacionCorreoSalida)
def cancelar_invitacion_correo(invitacion_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    invitacion = db.get(InvitacionCorreo, invitacion_id)
    if invitacion is None:
        raise HTTPException(status_code=404, detail="Invitación no encontrada")
    if invitacion.proyecto.creado_por_id != usuario.id:
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto puede cancelarla")
    if invitacion.solicitud_id is not None or invitacion.estado not in (EstadoSolicitud.PENDIENTE, EstadoSolicitud.ACEPTADA):
        raise HTTPException(status_code=409, detail="Esa invitación ya no se puede cancelar")
    invitacion.estado = EstadoSolicitud.CANCELADA
    invitacion.respondida_en = utcnow()
    db.commit()
    return InvitacionCorreoSalida.de(invitacion)


# ---- Para quien recibe el correo (sin sesión) ----------------------------------------------------

def _publica(db: Session, i: InvitacionCorreo) -> InvitacionPublica:
    cuenta = _cuenta(db, i.email)
    confirmada = cuenta is not None and cuenta.verificado
    return InvitacionPublica(
        email=i.email, estado=i.estado, vencida=_vencida(i), proyecto_id=i.proyecto_id,
        proyecto_titulo=i.proyecto.titulo, proyecto_resumen=i.proyecto.resumen,
        invitado_por=i.invitado_por.nombre if i.invitado_por else "El responsable del proyecto",
        rol_propuesto=i.rol_propuesto, aporte=i.aporte, habilidades=i.habilidades or [],
        disponibilidad_horas=i.disponibilidad_horas, motivacion=i.motivacion, mensaje=i.mensaje,
        cuenta_existe=confirmada, es_miembro=confirmada and es_miembro(db, i.proyecto, cuenta.id),
    )


def _abierta(i: InvitacionCorreo) -> None:
    if i.estado == EstadoSolicitud.CANCELADA:
        raise HTTPException(status_code=409, detail="El responsable retiró esta invitación.")
    if i.estado == EstadoSolicitud.RECHAZADA:
        raise HTTPException(status_code=409, detail="Ya rechazaste esta invitación.")
    if _vencida(i):
        raise HTTPException(status_code=410, detail="La invitación venció. Pide al responsable que te invite de nuevo.")


@publico.get("/{token}", response_model=InvitacionPublica)
def ver_invitacion(token: str, db: DbSession):
    return _publica(db, _por_token(db, token))


@publico.post("/{token}/aceptar", response_model=InvitacionPublica)
def aceptar_invitacion(token: str, db: DbSession, tareas: BackgroundTasks):
    """Acepta desde el enlace. Si la persona ya tiene cuenta, entra al equipo de una vez;
    si no, queda aceptada y se suma al equipo apenas cree la cuenta con ese correo."""
    invitacion = _por_token(db, token)
    if invitacion.estado != EstadoSolicitud.ACEPTADA:
        _abierta(invitacion)
        invitacion.estado = EstadoSolicitud.ACEPTADA
        invitacion.respondida_en = utcnow()
        db.commit()
    cuenta = _cuenta(db, invitacion.email)
    if cuenta is not None and cuenta.verificado and cuenta.activo:
        reclamar(db, cuenta, tareas)
    return _publica(db, invitacion)


@publico.post("/{token}/rechazar", response_model=InvitacionPublica)
def rechazar_invitacion(token: str, db: DbSession, tareas: BackgroundTasks):
    invitacion = _por_token(db, token)
    if invitacion.estado == EstadoSolicitud.ACEPTADA:
        raise HTTPException(status_code=409, detail="Ya aceptaste esta invitación.")
    _abierta(invitacion)
    invitacion.estado = EstadoSolicitud.RECHAZADA
    invitacion.respondida_en = utcnow()
    responsable = invitacion.invitado_por
    if responsable is not None:
        notificar(
            db, responsable, TipoNotificacion.SOLICITUD_RECHAZADA,
            f"{invitacion.email} rechazó la invitación a «{invitacion.proyecto.titulo}»",
            "La persona respondió desde el enlace que le llegó al correo.",
            f"/proyectos/{invitacion.proyecto_id}", tareas,
            detalles=[("Proyecto", invitacion.proyecto.titulo), ("Correo", invitacion.email)], boton="Ir al proyecto",
        )
    db.commit()
    return _publica(db, invitacion)


# ---- Al crear o confirmar una cuenta --------------------------------------------------------------

def reclamar(db: Session, usuario: Usuario, tareas: BackgroundTasks | None = None) -> int:
    """Convierte las invitaciones por correo de `usuario.email` en solicitudes de la plataforma.

    Se llama cuando una cuenta queda confirmada. Devuelve cuántas personas-proyecto se vincularon.
    """
    tareas = tareas if tareas is not None else BackgroundTasks()
    invitaciones = db.scalars(select(InvitacionCorreo).where(
        func.lower(InvitacionCorreo.email) == usuario.email.lower(), InvitacionCorreo.solicitud_id.is_(None),
        InvitacionCorreo.estado.in_([EstadoSolicitud.PENDIENTE, EstadoSolicitud.ACEPTADA]),
    ).order_by(InvitacionCorreo.creado_en)).all()
    vinculadas = 0
    for inv in invitaciones:
        if inv.estado == EstadoSolicitud.PENDIENTE and _vencida(inv):
            continue
        proyecto = inv.proyecto
        if es_miembro(db, proyecto, usuario.id):
            inv.estado = EstadoSolicitud.ACEPTADA
            db.commit()
            continue
        # Si ya había otra solicitud pendiente entre la persona y el proyecto, se usa esa.
        solicitud = db.scalar(select(Solicitud).where(
            Solicitud.proyecto_id == proyecto.id, Solicitud.usuario_id == usuario.id,
            Solicitud.estado == EstadoSolicitud.PENDIENTE,
        ))
        if solicitud is None:
            solicitud = Solicitud(
                proyecto=proyecto, usuario=usuario, tipo=TipoSolicitud.INVITACION, mensaje=inv.mensaje,
                tipo_aporte_id=inv.tipo_aporte_id, rol_propuesto=inv.rol_propuesto, aporte=inv.aporte,
                habilidades=inv.habilidades or [], disponibilidad_horas=inv.disponibilidad_horas,
                motivacion=inv.motivacion,
            )
            db.add(solicitud)
            db.flush()
        inv.solicitud_id = solicitud.id
        if inv.estado == EstadoSolicitud.ACEPTADA:
            solicitud.motivo_nombre = MOTIVO_ACEPTADA
            _cerrar(db, solicitud, EstadoSolicitud.ACEPTADA, usuario, tareas)  # agrega el miembro, XP, aviso y commit
        else:
            # Ya recibió el correo: aquí solo se deja el aviso en la campana.
            quien = inv.invitado_por.nombre if inv.invitado_por else "El responsable"
            db.add(Notificacion(
                usuario_id=usuario.id, tipo=TipoNotificacion.INVITACION_NUEVA,
                titulo=f"{quien} te invitó a «{proyecto.titulo}»",
                cuerpo=f"Te propone participar como {solicitud.rol_propuesto}. Acéptala o recházala desde tu perfil.",
                enlace=f"/perfil#solicitud-{solicitud.id}",
            ))
            db.commit()
        vinculadas += 1
    return vinculadas
