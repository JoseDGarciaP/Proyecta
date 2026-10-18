import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.core.database import Base, utcnow
from app.modules.usuarios.models import Usuario

# SQLite (pruebas) solo autoincrementa claves INTEGER; en PostgreSQL es BIGINT.
IdMensaje = BigInteger().with_variant(Integer, "sqlite")


class MensajeBase:
    """Columnas comunes a toda conversación. El id creciente sirve de cursor para pedir solo lo nuevo."""

    id: Mapped[int] = mapped_column(IdMensaje, primary_key=True, autoincrement=True)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    texto: Mapped[str] = mapped_column(Text)
    enviado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    editado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    eliminado: Mapped[bool] = mapped_column(Boolean, default=False)  # borrado lógico: el hilo no pierde su orden
    # Cambia al enviarlo, editarlo o eliminarlo: así quien consulta cada pocos segundos también se entera de esos cambios.
    modificado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    @declared_attr
    def autor(cls) -> Mapped[Usuario | None]:
        return relationship(lazy="joined")


class Mensaje(MensajeBase, Base):
    """Mensaje del chat del equipo de un proyecto."""

    __tablename__ = "proyecto_mensajes"
    __table_args__ = (
        Index("ix_proyecto_mensajes_proyecto_id_id", "proyecto_id", "id"),
        Index("ix_proyecto_mensajes_proyecto_id_modificado_en", "proyecto_id", "modificado_en"),
    )

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"))


class MensajeSolicitud(MensajeBase, Base):
    """Mensaje entre quien pide unirse (o fue invitado) y el responsable, antes de decidir."""

    __tablename__ = "solicitud_mensajes"
    __table_args__ = (
        Index("ix_solicitud_mensajes_solicitud_id_id", "solicitud_id", "id"),
        Index("ix_solicitud_mensajes_solicitud_id_modificado_en", "solicitud_id", "modificado_en"),
    )

    solicitud_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("solicitudes_alianza.id", ondelete="CASCADE"))


class Lectura(Base):
    """Hasta qué mensaje leyó cada persona el chat de un proyecto (para contar los no leídos)."""

    __tablename__ = "proyecto_chat_lecturas"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    ultimo_leido_id: Mapped[int] = mapped_column(IdMensaje, default=0)


class LecturaSolicitud(Base):
    """Lo mismo para la conversación de una solicitud."""

    __tablename__ = "solicitud_chat_lecturas"

    solicitud_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("solicitudes_alianza.id", ondelete="CASCADE"), primary_key=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    ultimo_leido_id: Mapped[int] = mapped_column(IdMensaje, default=0)
