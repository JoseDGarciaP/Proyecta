import enum
import uuid
from datetime import date

from sqlalchemy import JSON, BigInteger, CheckConstraint, Date, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, Timestamps, UuidPk
from app.modules.actores.models import Actor, proyecto_actores
from app.modules.catalogo.models import Area, Ods, proyecto_ods
from app.modules.usuarios.models import enum_col


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
    actores: Mapped[list[Actor]] = relationship(secondary=proyecto_actores, lazy="selectin")
