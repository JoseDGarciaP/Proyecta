import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UuidPk, utcnow
from app.modules.usuarios.models import enum_col


class TipoRecomendacion(str, enum.Enum):
    OPORTUNIDAD = "oportunidad"
    COLABORADOR = "colaborador"


class EstadoRecomendacion(str, enum.Enum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    ANULADA = "anulada"


class RecomendacionGuardada(UuidPk, Base):
    """Recomendación de la IA para un proyecto, guardada con su fecha y estado (HU-05).

    `objetivo_id` es la oportunidad o el usuario recomendado, según `tipo`.
    """

    __tablename__ = "recomendaciones"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    tipo: Mapped[TipoRecomendacion] = mapped_column(enum_col(TipoRecomendacion), index=True)
    objetivo_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    puntaje: Mapped[float] = mapped_column(Float, default=0.0)
    razon: Mapped[str] = mapped_column(Text, default="")
    estado: Mapped[EstadoRecomendacion] = mapped_column(
        enum_col(EstadoRecomendacion), default=EstadoRecomendacion.PENDIENTE, index=True
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
