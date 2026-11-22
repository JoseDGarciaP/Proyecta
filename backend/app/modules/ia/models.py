import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, Uuid
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
    # Ep5-Hu5/Hu6: quién la aceptó o anuló, cuándo y por qué. Una anulada no se vuelve a sugerir.
    motivo: Mapped[str] = mapped_column(Text, default="")
    decidido_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    decidido_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ValoracionDiagnostico(UuidPk, Base):
    """«¿Te sirvió?» sobre el diagnóstico y las mejoras sugeridas a un proyecto (Ep5-Hu9)."""

    __tablename__ = "valoraciones_diagnostico"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    util: Mapped[bool] = mapped_column(Boolean)
    comentario: Mapped[str] = mapped_column(Text, default="")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
