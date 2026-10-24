from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RolUsuario(Base):
    """Rol de una cuenta y sus permisos. Los del sistema (estudiante, docente...) no se eliminan;
    el admin puede crear otros (p. ej. «Coordinador de semillero»)."""

    __tablename__ = "roles"

    clave: Mapped[str] = mapped_column(String(40), primary_key=True)  # no cambia: la guardan los usuarios
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    permisos: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Exige correo de los dominios institucionales (todos menos aliado externo, por defecto).
    institucional: Mapped[bool] = mapped_column(Boolean, default=True)
    # Se puede elegir al crear la cuenta desde la página de registro.
    registro_publico: Mapped[bool] = mapped_column(Boolean, default=False)
    sistema: Mapped[bool] = mapped_column(Boolean, default=False)
    orden: Mapped[int] = mapped_column(Integer, default=0)
