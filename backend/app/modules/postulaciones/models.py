import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UuidPk, utcnow
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario, enum_col


class EstadoPostulacion(str, enum.Enum):
    ENVIADA = "enviada"
    ACEPTADA = "aceptada"
    NO_SELECCIONADA = "no_seleccionada"
    RETIRADA = "retirada"


class Postulacion(UuidPk, Base):
    """Un proyecto se postula a una oportunidad (convocatoria, fondo, mentoría…)."""

    __tablename__ = "postulaciones"
    __table_args__ = (UniqueConstraint("oportunidad_id", "proyecto_id", name="uq_postulacion_oportunidad_proyecto"),)

    oportunidad_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("oportunidades.id", ondelete="CASCADE"), index=True)
    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))  # quien postuló
    estado: Mapped[EstadoPostulacion] = mapped_column(enum_col(EstadoPostulacion), default=EstadoPostulacion.ENVIADA, index=True)
    nota: Mapped[str] = mapped_column(Text, default="")  # por qué el proyecto encaja
    comentario: Mapped[str] = mapped_column(Text, default="")  # respuesta de quien gestiona la oportunidad
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decidida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    oportunidad: Mapped[Oportunidad] = relationship(lazy="joined")
    proyecto: Mapped[Proyecto] = relationship(lazy="joined")
    usuario: Mapped[Usuario | None] = relationship(lazy="joined")
