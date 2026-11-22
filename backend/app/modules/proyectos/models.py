import enum
import uuid
from datetime import date

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, Timestamps, UuidPk, utcnow
from app.modules.actores.models import Actor, proyecto_actores
from app.modules.catalogo.models import Area, Ods, proyecto_areas, proyecto_ods
from app.modules.usuarios.models import Usuario, enum_col


class Estado(str, enum.Enum):
    IDEA = "idea"
    FORMULACION = "formulacion"
    EJECUCION = "ejecucion"
    FINALIZADO = "finalizado"
    PAUSADO = "pausado"


class Proyecto(UuidPk, Timestamps, Base):
    __tablename__ = "proyectos"
    __table_args__ = (
        CheckConstraint("avance BETWEEN 0 AND 100", name="avance_rango"),
        CheckConstraint("presupuesto >= 0", name="presupuesto_positivo"),
        CheckConstraint("fecha_fin IS NULL OR fecha_fin >= fecha_inicio", name="fechas_coherentes"),
    )

    titulo: Mapped[str] = mapped_column(String(200), index=True)
    resumen: Mapped[str] = mapped_column(String(300))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    necesidades: Mapped[str] = mapped_column(Text, default="")  # perfiles, financiación, equipos...
    problema: Mapped[str] = mapped_column(Text, default="", server_default="")  # Ep4-Hu17
    objetivos: Mapped[str] = mapped_column(Text, default="", server_default="")
    # Se archiva en lugar de borrarse si tiene colaboradores (Ep4-Hu20); no aparece en el explorador.
    archivado: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", index=True)
    archivado_motivo: Mapped[str] = mapped_column(Text, default="", server_default="")
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id"), index=True)
    estado: Mapped[Estado] = mapped_column(enum_col(Estado), default=Estado.IDEA, index=True)
    avance: Mapped[int] = mapped_column(SmallInteger, default=0)
    presupuesto: Mapped[int] = mapped_column(BigInteger, default=0)
    lider: Mapped[str] = mapped_column(String(150), default="")
    equipo: Mapped[list[str]] = mapped_column(JSON, default=list)
    etiquetas: Mapped[list[str]] = mapped_column(JSON, default=list)
    fecha_inicio: Mapped[date] = mapped_column(Date, default=date.today)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), index=True)

    area: Mapped[Area] = relationship(lazy="joined")
    ods: Mapped[list[Ods]] = relationship(secondary=proyecto_ods, lazy="selectin")
    areas_extra: Mapped[list[Area]] = relationship(secondary=proyecto_areas, lazy="selectin")
    actores: Mapped[list[Actor]] = relationship(secondary=proyecto_actores, lazy="selectin")
    # Quien registró el proyecto: de aquí sale el programa académico para filtrar (HU-03)
    creado_por: Mapped[Usuario | None] = relationship(foreign_keys=[creado_por_id], lazy="joined")


class CambioProyecto(UuidPk, Base):
    """Historial de cambios de un proyecto: quién, cuándo y qué campos (Ep4-Hu18)."""

    __tablename__ = "proyecto_cambios"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    cambios: Mapped[list[dict]] = mapped_column(JSON, default=list)  # [{campo, antes, despues}]
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    autor: Mapped[Usuario | None] = relationship(lazy="joined")


class AdjuntoProyecto(UuidPk, Base):
    """Archivo adjunto a la ficha de un proyecto: PDF, DOCX, PNG o JPG hasta 10 MB (Ep4-Hu22)."""

    __tablename__ = "proyecto_adjuntos"

    proyecto_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("proyectos.id", ondelete="CASCADE"), index=True)
    subido_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    nombre: Mapped[str] = mapped_column(String(255))
    ruta: Mapped[str] = mapped_column(String(255))
    tipo: Mapped[str] = mapped_column(String(100))
    tamano: Mapped[int] = mapped_column(BigInteger)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    subido_por: Mapped[Usuario | None] = relationship(lazy="joined")
