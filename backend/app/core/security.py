import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(subject: str, tipo: str, minutos: int, **extra: str) -> str:
    """`tipo` separa los usos: un token de verificación no sirve para entrar, ni al revés."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutos)
    datos = {**extra, "sub": subject, "tipo": tipo, "exp": expire}
    return jwt.encode(datos, get_settings().secret_key, algorithm=ALGORITHM)


def decode_payload(token: str, tipo: str) -> dict | None:
    """Datos del token si es válido, no venció y es del `tipo` pedido."""
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    return payload if payload.get("tipo") == tipo and payload.get("sub") else None


def decode_token(token: str, tipo: str) -> str | None:
    payload = decode_payload(token, tipo)
    return payload["sub"] if payload else None


def huella_password(hashed: str) -> str:
    """Cambia cuando cambia la contraseña: sirve para que un enlace de restablecer se use una sola vez."""
    return hashlib.sha256(hashed.encode()).hexdigest()[:16]


def create_access_token(subject: str) -> str:
    return create_token(subject, "acceso", get_settings().access_token_expire_minutes)


def decode_access_token(token: str) -> str | None:
    return decode_token(token, "acceso")
