import enum

from sqlalchemy import JSON, Boolean, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, Timestamps, UuidPk


class Rol(str, enum.Enum):
    ESTUDIANTE = "estudiante"
    DOCENTE = "docente"
    ADMINISTRATIVO = "administrativo"
    ALIADO = "aliado"
    ADMIN = "admin"


def enum_col(e: type[enum.Enum]) -> Enum:
    """Guarda el valor del enum como texto (sin tipo nativo en la base), fácil de migrar."""
    return Enum(e, native_enum=False, values_callable=lambda x: [m.value for m in x])


class Usuario(UuidPk, Timestamps, Base):
    __tablename__ = "usuarios"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    nombre: Mapped[str] = mapped_column(String(150))
    rol: Mapped[Rol] = mapped_column(enum_col(Rol), default=Rol.ESTUDIANTE)
    programa: Mapped[str | None] = mapped_column(String(150))  # programa académico o dependencia
    bio: Mapped[str | None] = mapped_column(Text)
    habilidades: Mapped[list[str]] = mapped_column(JSON, default=list)
    intereses: Mapped[list[str]] = mapped_column(JSON, default=list)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    # False hasta confirmar el correo (o entrar con Google, que ya lo verificó).
    verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True)  # id de la cuenta de Google
