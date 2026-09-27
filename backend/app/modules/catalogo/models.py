from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Area(Base):
    """Área de conocimiento (Tecnología, Ambiente, ...)."""

    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)


class Ods(Base):
    """Objetivo de Desarrollo Sostenible; el id es el número del ODS (1 a 17)."""

    __tablename__ = "ods"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nombre: Mapped[str] = mapped_column(String(120))


def _enlace(nombre: str, izq: tuple[str, str], der: tuple[str, str]) -> Table:
    """Tabla muchos a muchos. `izq` y `der` son (tabla, columna)."""
    return Table(
        nombre,
        Base.metadata,
        Column(izq[1], ForeignKey(f"{izq[0]}.id", ondelete="CASCADE"), primary_key=True),
        Column(der[1], ForeignKey(f"{der[0]}.id", ondelete="CASCADE"), primary_key=True),
    )


proyecto_ods = _enlace("proyecto_ods", ("proyectos", "proyecto_id"), ("ods", "ods_id"))
oportunidad_areas = _enlace("oportunidad_areas", ("oportunidades", "oportunidad_id"), ("areas", "area_id"))
oportunidad_ods = _enlace("oportunidad_ods", ("oportunidades", "oportunidad_id"), ("ods", "ods_id"))
