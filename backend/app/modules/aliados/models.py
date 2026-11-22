import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow
from app.modules.usuarios.models import Usuario, enum_col


class EstadoAliado(str, enum.Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


TIPOS_ALIADO = ["Empresa", "ONG o fundación", "Entidad pública", "Gremio o asociación", "Persona natural", "Otro"]


class PerfilAliado(Base):
    """Datos propios de un aliado externo (Ep4-Hu12 a Hu16). Uno a uno con `usuarios`.

    La cuenta no puede ingresar hasta que un administrador la apruebe (Ep4-Hu15).
    """

    __tablename__ = "perfiles_aliado"

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    razon_social: Mapped[str] = mapped_column(String(200), default="")
    tipo: Mapped[str] = mapped_column(String(60), default="Otro")
    documento: Mapped[str | None] = mapped_column(String(30), unique=True)  # NIT o cédula
    telefono: Mapped[str] = mapped_column(String(30), default="")
    sector: Mapped[str] = mapped_column(String(120), default="", index=True)
    sitio_web: Mapped[str] = mapped_column(String(300), default="")
    descripcion: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[EstadoAliado] = mapped_column(enum_col(EstadoAliado), default=EstadoAliado.PENDIENTE, index=True)
    motivo_rechazo: Mapped[str] = mapped_column(Text, default="")
    revisado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    revisado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    usuario: Mapped[Usuario] = relationship(foreign_keys=[usuario_id], lazy="joined")
