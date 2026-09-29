"""Verifica el ID token que Google entrega al botón «Continuar con Google».

Se valida la firma con las llaves públicas de Google, la audiencia (nuestro ID de cliente),
el emisor y la vigencia. No se usan secretos: el ID de cliente es público.
"""

from functools import lru_cache

import jwt

from app.core.config import get_settings

CERTS = "https://www.googleapis.com/oauth2/v3/certs"
EMISORES = ("accounts.google.com", "https://accounts.google.com")


class TokenGoogleInvalido(Exception):
    pass


@lru_cache
def _llaves() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(CERTS, cache_keys=True)


def verificar(credential: str) -> dict:
    """Devuelve los datos de la cuenta (sub, email, email_verified, name, hd…)."""
    client_id = get_settings().google_client_id
    if not client_id:
        raise TokenGoogleInvalido("El ingreso con Google no está configurado")
    try:
        llave = _llaves().get_signing_key_from_jwt(credential)
        datos = jwt.decode(credential, llave.key, algorithms=["RS256"], audience=client_id)
    except jwt.PyJWTError as error:
        raise TokenGoogleInvalido(str(error)) from error
    if datos.get("iss") not in EMISORES:
        raise TokenGoogleInvalido("Emisor inválido")
    return datos
