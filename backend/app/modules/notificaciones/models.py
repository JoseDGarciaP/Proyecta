import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UuidPk, utcnow
from app.modules.usuarios.models import enum_col


class TipoNotificacion(str, enum.Enum):
    SOLICITUD_NUEVA = "solicitud_nueva"
    INVITACION_NUEVA = "invitacion_nueva"
    SOLICITUD_ACEPTADA = "solicitud_aceptada"
    SOLICITUD_RECHAZADA = "solicitud_rechazada"
    SOLICITUD_CANCELADA = "solicitud_cancelada"
    MENSAJES_SIN_LEER = "mensajes_sin_leer"
    CUENTA = "cuenta"  # cambios hechos por un admin: rol, activación, cuenta creada
    MODERACION = "moderacion"  # un admin quitó un proyecto
    INSIGNIA = "insignia"  # ganó una insignia o logro
    NIVEL = "nivel"  # subió de nivel o recibió experiencia
    EVIDENCIA = "evidencia"  # revisaron su certificado o evidencia
    POSTULACION = "postulacion"  # cambió el estado de una postulación de su proyecto
    REVISION = "revision"  # para quien administra: algo nuevo por revisar


# Categoría de correo de cada tipo (ver Ajustes y Usuario.correo_avisos).
CATEGORIA = {
    TipoNotificacion.SOLICITUD_NUEVA: "solicitudes",
    TipoNotificacion.INVITACION_NUEVA: "solicitudes",
    TipoNotificacion.SOLICITUD_ACEPTADA: "respuestas",
    TipoNotificacion.SOLICITUD_RECHAZADA: "respuestas",
    TipoNotificacion.SOLICITUD_CANCELADA: "respuestas",
    TipoNotificacion.MENSAJES_SIN_LEER: "mensajes",
    TipoNotificacion.CUENTA: "cuenta",
    TipoNotificacion.MODERACION: "cuenta",
    TipoNotificacion.INSIGNIA: "logros",
    TipoNotificacion.NIVEL: "logros",
    TipoNotificacion.EVIDENCIA: "respuestas",
    TipoNotificacion.POSTULACION: "respuestas",
    TipoNotificacion.REVISION: "solicitudes",
}


class Notificacion(UuidPk, Base):
    """Alerta dentro de la plataforma (la campana). Si corresponde, también se envía por correo."""

    __tablename__ = "notificaciones"
    __table_args__ = (Index("ix_notificaciones_usuario_id_creada_en", "usuario_id", "creada_en"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    tipo: Mapped[TipoNotificacion] = mapped_column(enum_col(TipoNotificacion))
    titulo: Mapped[str] = mapped_column(String(200))
    cuerpo: Mapped[str] = mapped_column(Text, default="")
    enlace: Mapped[str] = mapped_column(String(300), default="")  # ruta de la interfaz, p. ej. /perfil
    leida: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    correo_enviado: Mapped[bool] = mapped_column(Boolean, default=False)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
