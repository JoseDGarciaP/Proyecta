import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UuidPk, utcnow
from app.modules.usuarios.models import Usuario


class Observacion(UuidPk, Base):
    """Comentario público en la ficha de un proyecto (Ep4-Hu23). El admin puede ocultarlo (Ep4-Hu27)."""

    __tablename__ = "observaciones"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    texto: Mapped[str] = mapped_column(Text)
    oculta: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", index=True)
    motivo_oculta: Mapped[str] = mapped_column(Text, default="", server_default="")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    editado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    autor: Mapped[Usuario | None] = relationship(lazy="joined")
