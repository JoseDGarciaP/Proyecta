import uuid
from collections.abc import Generator
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Uuid, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import get_settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UuidPk:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class Timestamps:
    creado_en: Mapped[date] = mapped_column(Date, default=date.today)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


def opciones_conexion(url: str) -> dict:
    """El pooler de Supabase en modo transacción (puerto 6543) no admite sentencias preparadas."""
    return {"prepare_threshold": None} if ":6543/" in url else {}


def _opciones_motor(url: str) -> dict:
    if not url.startswith("postgresql"):
        return {}
    # Pocas conexiones: el plan gratuito de Supabase limita las del pooler.
    return {"pool_size": 3, "max_overflow": 5, "connect_args": opciones_conexion(url)}


_url = get_settings().database_url
engine = create_engine(_url, pool_pre_ping=True, **_opciones_motor(_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
