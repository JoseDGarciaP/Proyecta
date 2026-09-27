import enum
import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, Timestamps, UuidPk
from app.modules.catalogo.models import Area, Ods, oportunidad_areas, oportunidad_ods
from app.modules.usuarios.models import enum_col


class TipoOportunidad(str, enum.Enum):
    CONVOCATORIA = "convocatoria"
    FINANCIACION = "financiacion"
    MENTORIA = "mentoria"
    INFRAESTRUCTURA = "infraestructura"


class Oportunidad(UuidPk, Timestamps, Base):
    """Convocatoria, fondo, mentoría o acceso a infraestructura. Por ahora las carga un administrador."""

    __tablename__ = "oportunidades"

    titulo: Mapped[str] = mapped_column(String(200), index=True)
    entidad: Mapped[str] = mapped_column(String(150), default="")
    tipo: Mapped[TipoOportunidad] = mapped_column(enum_col(TipoOportunidad))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    monto: Mapped[int | None] = mapped_column(BigInteger)
    cierra_en: Mapped[date] = mapped_column(Date, index=True)
    url: Mapped[str] = mapped_column(String(500), default="")
    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))

    areas: Mapped[list[Area]] = relationship(secondary=oportunidad_areas, lazy="selectin")
    ods: Mapped[list[Ods]] = relationship(secondary=oportunidad_ods, lazy="selectin")
