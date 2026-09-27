import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, Timestamps, UuidPk, utcnow
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario, enum_col


class TipoSolicitud(str, enum.Enum):
    SOLICITUD = "solicitud"  # el usuario pide unirse; responde quien registró el proyecto
    INVITACION = "invitacion"  # quien registró el proyecto invita; responde el usuario


class EstadoSolicitud(str, enum.Enum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"


class Miembro(Base):
    """Colaborador aceptado en un proyecto (quien lo registró no necesita fila aquí)."""

    __tablename__ = "proyecto_miembros"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True, index=True)
    rol: Mapped[str] = mapped_column(String(80), default="colaborador")
    desde: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    usuario: Mapped[Usuario] = relationship(lazy="joined")
    proyecto: Mapped[Proyecto] = relationship(lazy="joined")


class Solicitud(UuidPk, Timestamps, Base):
    """Historial de alianzas: pedidos de unión e invitaciones con su respuesta."""

    __tablename__ = "solicitudes_alianza"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[TipoSolicitud] = mapped_column(enum_col(TipoSolicitud))
    estado: Mapped[EstadoSolicitud] = mapped_column(enum_col(EstadoSolicitud), default=EstadoSolicitud.PENDIENTE, index=True)
    mensaje: Mapped[str] = mapped_column(Text, default="")
    respuesta: Mapped[str] = mapped_column(Text, default="")
    respondida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    usuario: Mapped[Usuario] = relationship(lazy="joined")
    proyecto: Mapped[Proyecto] = relationship(lazy="joined")
