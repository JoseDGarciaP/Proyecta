import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, Timestamps, UuidPk
from app.modules.roles.models import RolUsuario


class Rol(str, enum.Enum):
    """Roles del sistema (siempre existen). El admin puede crear otros en la tabla `roles`."""

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
    # Clave del rol (tabla `roles`): uno del sistema (ver Rol) o uno creado por el admin.
    rol: Mapped[str] = mapped_column(String(40), ForeignKey("roles.clave"), default=Rol.ESTUDIANTE.value, index=True)
    rol_def: Mapped[RolUsuario | None] = relationship(lazy="joined")
    programa: Mapped[str | None] = mapped_column(String(150))  # programa académico o dependencia
    bio: Mapped[str | None] = mapped_column(Text)
    habilidades: Mapped[list[str]] = mapped_column(JSON, default=list)
    intereses: Mapped[list[str]] = mapped_column(JSON, default=list)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    # False hasta confirmar el correo (o entrar con Google, que ya lo verificó).
    verificado: Mapped[bool] = mapped_column(Boolean, default=False)
    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True)  # id de la cuenta de Google
    # Qué correos de alerta quiere recibir (las alertas dentro de la plataforma siempre llegan).
    correo_avisos: Mapped[dict[str, bool]] = mapped_column(JSON, default=lambda: dict(AVISOS_POR_DEFECTO))
    # Experiencia acumulada y nivel alcanzado (se recalculan en app.modules.experiencia.servicio).
    xp: Mapped[int] = mapped_column(Integer, default=0)
    nivel_id: Mapped[int | None] = mapped_column(ForeignKey("niveles.id", ondelete="SET NULL"))
    # Hasta qué momento ya se le avisó por correo de mensajes sin leer (para no repetir el aviso).
    resumen_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @property
    def rol_nombre(self) -> str:
        return self.rol_def.nombre if self.rol_def else self.rol

    def quiere_correo(self, categoria: str) -> bool:
        return bool({**AVISOS_POR_DEFECTO, **(self.correo_avisos or {})}.get(categoria, True))


# Categorías que cada persona puede apagar. Los avisos de su cuenta (los manda un admin) no se pueden apagar.
AVISOS_POR_DEFECTO = {"solicitudes": True, "respuestas": True, "mensajes": True, "logros": True}
