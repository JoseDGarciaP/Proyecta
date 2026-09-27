import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.alianzas.models import EstadoSolicitud, Miembro, Solicitud, TipoSolicitud


class NuevaSolicitud(BaseModel):
    mensaje: str = Field(default="", max_length=1000)


class NuevaInvitacion(NuevaSolicitud):
    usuario_id: uuid.UUID


class Respuesta(BaseModel):
    respuesta: str = Field(default="", max_length=1000)


class SolicitudSalida(BaseModel):
    id: uuid.UUID
    tipo: TipoSolicitud
    estado: EstadoSolicitud
    proyecto_id: uuid.UUID
    proyecto_titulo: str
    usuario_id: uuid.UUID
    usuario_nombre: str
    mensaje: str
    respuesta: str
    creado_en: date
    respondida_en: datetime | None
    por_responder: bool  # True si quien consulta es quien debe aceptar o rechazar

    @classmethod
    def de(cls, s: Solicitud, yo: uuid.UUID) -> "SolicitudSalida":
        return cls(
            id=s.id, tipo=s.tipo, estado=s.estado, proyecto_id=s.proyecto_id, proyecto_titulo=s.proyecto.titulo,
            usuario_id=s.usuario_id, usuario_nombre=s.usuario.nombre, mensaje=s.mensaje, respuesta=s.respuesta,
            creado_en=s.creado_en, respondida_en=s.respondida_en,
            por_responder=s.estado == EstadoSolicitud.PENDIENTE and responde(s) == yo,
        )


class MiembroSalida(BaseModel):
    usuario_id: uuid.UUID
    nombre: str
    programa: str | None
    rol: str
    desde: datetime

    @classmethod
    def de(cls, m: Miembro) -> "MiembroSalida":
        return cls(usuario_id=m.usuario_id, nombre=m.usuario.nombre, programa=m.usuario.programa, rol=m.rol, desde=m.desde)


def responde(s: Solicitud) -> uuid.UUID | None:
    """Quién decide sobre la solicitud: el dueño del proyecto o el invitado."""
    return s.proyecto.creado_por_id if s.tipo == TipoSolicitud.SOLICITUD else s.usuario_id
