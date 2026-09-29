from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(subject: str, tipo: str, minutos: int) -> str:
    """`tipo` separa los usos: un token de verificación no sirve para entrar, ni al revés."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutos)
    return jwt.encode({"sub": subject, "tipo": tipo, "exp": expire}, get_settings().secret_key, algorithm=ALGORITHM)


def decode_token(token: str, tipo: str) -> str | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    return payload.get("sub") if payload.get("tipo") == tipo else None


def create_access_token(subject: str) -> str:
    return create_token(subject, "acceso", get_settings().access_token_expire_minutes)


def decode_access_token(token: str) -> str | None:
    return decode_token(token, "acceso")
