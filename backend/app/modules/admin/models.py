import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UuidPk, utcnow
from app.modules.usuarios.models import Usuario


class RegistroAdmin(UuidPk, Base):
    """Bitácora de lo que hacen los administradores (quién, qué y cuándo)."""

    __tablename__ = "registro_admin"

    admin_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    accion: Mapped[str] = mapped_column(String(80))  # p. ej. usuario.rol, motivo.crear, proyecto.eliminar
    objeto: Mapped[str] = mapped_column(String(250), default="")  # sobre qué (nombre legible)
    detalle: Mapped[str] = mapped_column(Text, default="")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    admin: Mapped[Usuario | None] = relationship(lazy="joined")
