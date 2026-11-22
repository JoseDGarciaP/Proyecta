import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UuidPk, utcnow
from app.modules.usuarios.models import Usuario, enum_col


class EstadoAporte(str, enum.Enum):
    PENDIENTE = "pendiente"
    VALIDADO = "validado"
    RECHAZADO = "rechazado"


class Aporte(UuidPk, Base):
    """Lo que un miembro aportó al proyecto (horas, dinero, materiales…), que el responsable valida (Ep6-Hu11)."""

    __tablename__ = "aportes"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)
    tipo: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text)
    horas: Mapped[int | None] = mapped_column(Integer)
    valor: Mapped[int | None] = mapped_column(Integer)  # en pesos, si aplica
    fecha: Mapped[date] = mapped_column(Date)
    estado: Mapped[EstadoAporte] = mapped_column(enum_col(EstadoAporte), default=EstadoAporte.PENDIENTE, index=True)
    comentario: Mapped[str] = mapped_column(Text, default="")  # de quien valida
    validado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    validado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    usuario: Mapped[Usuario | None] = relationship(foreign_keys=[usuario_id], lazy="joined")
