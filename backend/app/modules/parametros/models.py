"""Parámetros que el administrador configura sin tocar el código."""

import enum

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.usuarios.models import enum_col


class TipoMotivo(str, enum.Enum):
    APROBACION = "aprobacion"
    RECHAZO = "rechazo"


class Motivo(Base):
    """Motivo para aprobar o rechazar una colaboración. Elegir uno es obligatorio al decidir."""

    __tablename__ = "motivos_decision"

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[TipoMotivo] = mapped_column(enum_col(TipoMotivo), index=True)
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str] = mapped_column(Text, default="")
    # Para motivos como «Otro»: obliga a escribir el comentario.
    requiere_comentario: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)


class TipoAporte(Base):
    """Rol o tipo de aporte que se propone en una solicitud o invitación (desarrollo, diseño...)."""

    __tablename__ = "tipos_aporte"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    descripcion: Mapped[str] = mapped_column(Text, default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)


class ParaPlantilla(str, enum.Enum):
    SOLICITANTE = "solicitante"  # quien pide unirse o fue invitado
    RESPONSABLE = "responsable"  # quien registró el proyecto
    TODOS = "todos"


class Plantilla(Base):
    """Mensaje tipo para la conversación de una solicitud. Se inserta en el chat y se puede editar."""

    __tablename__ = "plantillas_mensaje"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    texto: Mapped[str] = mapped_column(Text)
    para: Mapped[ParaPlantilla] = mapped_column(enum_col(ParaPlantilla), default=ParaPlantilla.TODOS)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)


class Ajuste(Base):
    """Ajuste general (clave → valor JSON). Los valores por defecto están en parametros.ajustes."""

    __tablename__ = "ajustes"

    clave: Mapped[str] = mapped_column(String(80), primary_key=True)
    valor: Mapped[object] = mapped_column(JSON)
