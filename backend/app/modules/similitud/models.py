import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utcnow


class Embedding(Base):
    """Vector de un proyecto, oportunidad o perfil de usuario.

    Se guarda en pgvector (en SQLite, para las pruebas, como JSON). `huella` resume el texto
    y el modelo con que se calculó: si cambia alguno, el vector se recalcula.
    """

    __tablename__ = "embeddings"

    entidad: Mapped[str] = mapped_column(String(20), primary_key=True)  # proyecto | oportunidad | usuario
    entidad_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    modelo: Mapped[str] = mapped_column(String(200))
    huella: Mapped[str] = mapped_column(String(64))
    # Sin dimensión fija para poder cambiar de modelo; se filtra siempre por `modelo`.
    vector: Mapped[list[float]] = mapped_column(Vector().with_variant(JSON(), "sqlite"))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
