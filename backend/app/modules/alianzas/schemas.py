import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.alianzas.models import EstadoSolicitud, Miembro, Solicitud, TipoSolicitud


class Recomendacion(BaseModel):
    """Formato fijo para pedir unirse o invitar a alguien."""

    tipo_aporte_id: int = Field(description="Rol o tipo de aporte (catálogo que configura el admin)")
    aporte: str = Field(min_length=10, max_length=1000, description="Qué puede aportar o qué se espera de la persona")
    habilidades: list[str] = Field(default_factory=list, max_length=15)
    disponibilidad_horas: int = Field(ge=1, le=60, description="Horas por semana")
    motivacion: str = Field(min_length=10, max_length=1000, description="Por qué le interesa o por qué se le invita")
    mensaje: str = Field(default="", max_length=1000, description="Nota adicional opcional")

    @field_validator("aporte", "motivacion", "mensaje")
    @classmethod
    def recortar(cls, v: str) -> str:
        return v.strip()

    @field_validator("habilidades")
    @classmethod
    def limpiar(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(h.strip()[:60] for h in v if h.strip()))


class NuevaSolicitud(Recomendacion):
    pass


class NuevaInvitacion(Recomendacion):
    usuario_id: uuid.UUID


class Decision(BaseModel):
    motivo_id: int
    respuesta: str = Field(default="", max_length=1000, description="Comentario opcional (obligatorio si el motivo lo pide)")


class SolicitudSalida(BaseModel):
    id: uuid.UUID
    tipo: TipoSolicitud
    estado: EstadoSolicitud
    proyecto_id: uuid.UUID
    proyecto_titulo: str
    usuario_id: uuid.UUID
    usuario_nombre: str
    mensaje: str
    tipo_aporte_id: int | None
    rol_propuesto: str
    aporte: str
    habilidades: list[str]
    disponibilidad_horas: int | None
    motivacion: str
    motivo_id: int | None
    motivo_nombre: str
    respuesta: str
    creado_en: date
    respondida_en: datetime | None
    por_responder: bool  # True si quien consulta es quien debe aceptar o rechazar

    @classmethod
    def de(cls, s: Solicitud, yo: uuid.UUID) -> "SolicitudSalida":
        return cls(
            id=s.id, tipo=s.tipo, estado=s.estado, proyecto_id=s.proyecto_id, proyecto_titulo=s.proyecto.titulo,
            usuario_id=s.usuario_id, usuario_nombre=s.usuario.nombre, mensaje=s.mensaje,
            tipo_aporte_id=s.tipo_aporte_id, rol_propuesto=s.rol_propuesto or "", aporte=s.aporte or "",
            habilidades=s.habilidades or [], disponibilidad_horas=s.disponibilidad_horas, motivacion=s.motivacion or "",
            motivo_id=s.motivo_id, motivo_nombre=s.motivo_nombre or "", respuesta=s.respuesta,
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


def envia(s: Solicitud) -> uuid.UUID | None:
    """Quién la envió: el solicitante o el dueño del proyecto (en una invitación)."""
    return s.usuario_id if s.tipo == TipoSolicitud.SOLICITUD else s.proyecto.creado_por_id
