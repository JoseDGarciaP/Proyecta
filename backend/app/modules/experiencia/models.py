import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UuidPk, utcnow
from app.modules.usuarios.models import Usuario


class AccionXP(Base):
    """Cuántos puntos de experiencia da cada acción. El admin ajusta puntos, tope diario y si está activa."""

    __tablename__ = "acciones_xp"

    clave: Mapped[str] = mapped_column(String(40), primary_key=True)  # la usa el código (ver seed.ACCIONES)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    puntos: Mapped[int] = mapped_column(Integer, default=10)
    tope_diario: Mapped[int | None] = mapped_column(Integer)  # veces por día que suma; vacío = sin tope
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)


class MovimientoXP(UuidPk, Base):
    """Historial de experiencia: de dónde salió cada punto. `referencia` evita sumar dos veces lo mismo
    (p. ej. el mismo proyecto registrado); los ajustes del admin pueden ser negativos."""

    __tablename__ = "movimientos_xp"
    __table_args__ = (
        UniqueConstraint("usuario_id", "accion", "referencia", name="uq_movimiento_xp_referencia"),
        Index("ix_movimientos_xp_usuario_id_creado_en", "usuario_id", "creado_en"),
        Index("ix_movimientos_xp_creado_en", "creado_en"),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    accion: Mapped[str] = mapped_column(String(40))  # clave de AccionXP, «ajuste» o «evidencia»
    puntos: Mapped[int] = mapped_column(Integer)
    detalle: Mapped[str] = mapped_column(Text, default="")
    referencia: Mapped[str | None] = mapped_column(String(120))
    otorgado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    otorgado_por: Mapped[Usuario | None] = relationship(lazy="joined", foreign_keys=[otorgado_por_id])


class Nivel(Base):
    """Nivel de experiencia (Novato, Curioso…). Se alcanza con XP mínima, cierta cantidad de insignias
    vigentes y, si se quiere, insignias obligatorias. Los niveles se suben en orden."""

    __tablename__ = "niveles"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), unique=True)
    descripcion: Mapped[str] = mapped_column(Text, default="")
    icono: Mapped[str] = mapped_column(String(30), default="star")  # mismos íconos que las insignias
    color: Mapped[str] = mapped_column(String(20), default="slate")
    xp_minima: Mapped[int] = mapped_column(Integer, default=0)
    insignias_minimas: Mapped[int] = mapped_column(Integer, default=0)
    insignias_requeridas: Mapped[list[int]] = mapped_column(JSON, default=list)
