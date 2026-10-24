import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UuidPk, utcnow
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario, enum_col


class TipoEvidencia(str, enum.Enum):
    CERTIFICADO = "certificado"
    CONSTANCIA = "constancia"  # de participación, asistencia…
    INFORME = "informe"
    FOTO = "foto"
    OTRO = "otro"


class EstadoEvidencia(str, enum.Enum):
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"


class Evidencia(UuidPk, Base):
    """Certificado o archivo que sube una persona (opcionalmente de un proyecto). Un admin lo revisa
    y decide cuánta experiencia da."""

    __tablename__ = "evidencias"

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    proyecto_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("proyectos.id", ondelete="SET NULL"), index=True)
    titulo: Mapped[str] = mapped_column(String(200))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    tipo: Mapped[TipoEvidencia] = mapped_column(enum_col(TipoEvidencia), default=TipoEvidencia.CERTIFICADO)
    archivo_nombre: Mapped[str] = mapped_column(String(255))  # nombre original
    archivo_ruta: Mapped[str] = mapped_column(String(255))  # nombre en disco (aleatorio)
    archivo_tipo: Mapped[str] = mapped_column(String(100))
    archivo_tamano: Mapped[int] = mapped_column(Integer)
    estado: Mapped[EstadoEvidencia] = mapped_column(enum_col(EstadoEvidencia), default=EstadoEvidencia.PENDIENTE, index=True)
    xp_otorgada: Mapped[int] = mapped_column(Integer, default=0)
    comentario: Mapped[str] = mapped_column(Text, default="")  # del admin al revisar
    revisada_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    revisada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

    usuario: Mapped[Usuario] = relationship(lazy="joined", foreign_keys=[usuario_id])
    proyecto: Mapped[Proyecto | None] = relationship(lazy="joined")
    revisada_por: Mapped[Usuario | None] = relationship(lazy="joined", foreign_keys=[revisada_por_id])
