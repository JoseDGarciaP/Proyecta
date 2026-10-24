import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, SmallInteger, String, Text
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
    mensaje: Mapped[str] = mapped_column(Text, default="")  # nota adicional opcional

    # Formato fijo de la recomendación. En una solicitud lo llena quien pide unirse (lo que ofrece);
    # en una invitación, el responsable (lo que propone y espera).
    tipo_aporte_id: Mapped[int | None] = mapped_column(ForeignKey("tipos_aporte.id", ondelete="SET NULL"))
    rol_propuesto: Mapped[str] = mapped_column(String(120), default="")  # nombre del tipo de aporte al enviarla
    aporte: Mapped[str] = mapped_column(Text, default="")
    habilidades: Mapped[list[str]] = mapped_column(JSON, default=list)
    disponibilidad_horas: Mapped[int | None] = mapped_column(SmallInteger)  # horas por semana
    motivacion: Mapped[str] = mapped_column(Text, default="")

    # Decisión: motivo del catálogo (obligatorio al aprobar o rechazar) y comentario opcional.
    motivo_id: Mapped[int | None] = mapped_column(ForeignKey("motivos_decision.id", ondelete="SET NULL"))
    motivo_nombre: Mapped[str] = mapped_column(String(150), default="")  # se guarda el texto por si luego lo editan
    respuesta: Mapped[str] = mapped_column(Text, default="")  # comentario de quien decide
    respondida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    usuario: Mapped[Usuario] = relationship(lazy="joined")
    proyecto: Mapped[Proyecto] = relationship(lazy="joined")
