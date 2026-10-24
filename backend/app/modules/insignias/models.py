import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, UuidPk, utcnow
from app.modules.usuarios.models import Usuario

TIPOS = {
    "logro": "Logro",  # por méritos medibles en la plataforma
    "condecoracion": "Condecoración",  # distinción formal, p. ej. de una facultad o un evento
    "reconocimiento": "Reconocimiento",  # agradecimiento o mención por un aporte
}


class Insignia(Base):
    """Insignia que define el admin.

    `reglas` = {"modo": "todas" | "alguna", "condiciones": [{"criterio", "umbral", "valor"}]}.
    Con reglas se otorga sola a quien las cumple; sin reglas la otorga un administrador con un motivo.
    """

    __tablename__ = "insignias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str] = mapped_column(Text, default="")  # qué significa
    tipo: Mapped[str] = mapped_column(String(20), default="logro")  # ver TIPOS
    entidad: Mapped[str] = mapped_column(String(150), default="")  # «En nombre de» (condecoraciones)
    icono: Mapped[str] = mapped_column(String(30), default="award")  # ver servicio.ICONOS
    color: Mapped[str] = mapped_column(String(20), default="amber")  # ver servicio.COLORES
    reglas: Mapped[dict | None] = mapped_column(JSON(none_as_null=True))
    # Vigencia: fecha fija (p. ej. fin de semestre) y/o días desde que se otorga. Vacío = no vence.
    vence_en: Mapped[date | None] = mapped_column(Date)
    vigencia_dias: Mapped[int | None] = mapped_column(Integer)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def condiciones(self) -> list[dict]:
        return list((self.reglas or {}).get("condiciones") or [])

    @property
    def automatica(self) -> bool:
        return bool(self.condiciones)

    @property
    def modo(self) -> str:
        return (self.reglas or {}).get("modo") or "todas"


class UsuarioInsignia(UuidPk, Base):
    """Insignia otorgada. Si se retira queda con `retirada_en` (así la regla automática no la vuelve a dar);
    si vence (`vence_en`) deja de mostrarse como vigente y queda en el historial."""

    __tablename__ = "usuario_insignias"
    __table_args__ = (UniqueConstraint("usuario_id", "insignia_id", name="uq_usuario_insignia"),)

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    insignia_id: Mapped[int] = mapped_column(ForeignKey("insignias.id", ondelete="CASCADE"), index=True)
    motivo: Mapped[str] = mapped_column(Text, default="")
    automatica: Mapped[bool] = mapped_column(Boolean, default=False)
    otorgada_por_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    otorgada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    fecha_evento: Mapped[date | None] = mapped_column(Date)  # p. ej. el día de la ceremonia o la feria
    vence_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retirada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    insignia: Mapped[Insignia] = relationship(lazy="joined")
    usuario: Mapped[Usuario] = relationship(lazy="joined", foreign_keys=[usuario_id])
    otorgada_por: Mapped[Usuario | None] = relationship(lazy="joined", foreign_keys=[otorgada_por_id])
