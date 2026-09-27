import enum

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, Timestamps, UuidPk
from app.modules.usuarios.models import enum_col


class TipoActor(str, enum.Enum):
    UNIVERSIDAD = "universidad"
    EMPRESA = "empresa"
    ESTADO = "estado"
    COMUNIDAD = "comunidad"
    ONG = "ong"


class Actor(UuidPk, Timestamps, Base):
    """Organización aliada: empresa, entidad del Estado, comunidad, ONG o dependencia universitaria."""

    __tablename__ = "actores"

    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[TipoActor] = mapped_column(enum_col(TipoActor))
    sector: Mapped[str] = mapped_column(String(150), default="")
    contacto: Mapped[str] = mapped_column(String(200), default="")


proyecto_actores = Table(
    "proyecto_actores",
    Base.metadata,
    Column("proyecto_id", ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True),
    Column("actor_id", ForeignKey("actores.id", ondelete="CASCADE"), primary_key=True),
    Column("rol", String(60), nullable=False, default="aliado"),
)
