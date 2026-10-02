"""Comprobaciones para aceptar solo correos que de verdad pueden recibir mensajes.

Se hacen antes de crear la cuenta, de la más barata a la más costosa:
  1. Formato (RFC 5322) y normalización (minúsculas, sin espacios).
  2. Errores de tipeo en dominios comunes: «gmial.com» → sugiere «gmail.com».
  3. Dominios de correo temporal o desechable (lista pública mantenida por la comunidad).
  4. DNS: el dominio debe tener registros MX (o A) que acepten correo.
El paso final, que demuestra que la persona controla el buzón, es el enlace de confirmación.
"""

import logging
from dataclasses import dataclass
from functools import lru_cache

import dns.exception
import dns.resolver
from disposable_email_domains import blocklist as DESECHABLES
from email_validator import EmailNotValidError, validate_email

from app.core.config import get_settings

log = logging.getLogger("proyecta.correo")

# Dominios frecuentes para detectar errores de tipeo. El institucional va primero.
DOMINIOS_COMUNES = (
    "ufpso.edu.co",
    "gmail.com",
    "hotmail.com",
    "outlook.com",
    "outlook.es",
    "hotmail.es",
    "yahoo.com",
    "yahoo.es",
    "icloud.com",
    "live.com",
)

# Dominios reales que se parecen a los comunes y no deben corregirse.
PARECIDOS_REALES = frozenset({
    "ufps.edu.co", "mail.com", "email.com", "gmx.com", "gmx.es", "aol.com",
    "mail.ru", "ymail.com", "rocketmail.com",
})


class CorreoNoValido(ValueError):
    def __init__(self, mensaje: str, sugerencia: str | None = None):
        super().__init__(mensaje)
        self.sugerencia = sugerencia


@dataclass(frozen=True)
class CorreoValidado:
    email: str
    dominio: str


def _distancia(a: str, b: str) -> int:
    """Levenshtein con transposiciones (Damerau restringida): «gmial» está a 1 de «gmail»."""
    filas = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        filas[i][0] = i
    for j in range(len(b) + 1):
        filas[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            costo = 0 if a[i - 1] == b[j - 1] else 1
            filas[i][j] = min(filas[i - 1][j] + 1, filas[i][j - 1] + 1, filas[i - 1][j - 1] + costo)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                filas[i][j] = min(filas[i][j], filas[i - 2][j - 2] + 1)
    return filas[-1][-1]


def sugerir_dominio(dominio: str) -> str | None:
    if dominio in DOMINIOS_COMUNES or dominio in PARECIDOS_REALES:
        return None
    candidatos = [(d, _distancia(dominio, d)) for d in DOMINIOS_COMUNES]
    mejor, distancia = min(candidatos, key=lambda c: c[1])
    # Un solo cambio (letra de más, de menos, cambiada o dos letras invertidas). Con dos cambios
    # aparecen dominios reales distintos (p. ej. «yopmail.com» frente a «hotmail.com»).
    return mejor if distancia == 1 else None


@lru_cache(maxsize=2048)
def dominio_recibe_correo(dominio: str) -> bool | None:
    """True si hay MX (o un A como respaldo, RFC 5321), False si el dominio no existe o rechaza correo.

    None si no se pudo consultar (sin red, DNS caído): en ese caso no se bloquea a la persona,
    porque el enlace de confirmación igual protege. El resultado se guarda en caché.
    """
    resolver = dns.resolver.Resolver()
    resolver.lifetime = get_settings().correo_dns_timeout
    try:
        respuesta = resolver.resolve(dominio, "MX")
        # «MX 0 .» (Null MX, RFC 7505) significa que el dominio declara no recibir correo.
        return any(str(r.exchange) not in (".", "") for r in respuesta)
    except dns.resolver.NXDOMAIN:
        return False
    except dns.resolver.NoAnswer:
        try:
            resolver.resolve(dominio, "A")
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return False
        except dns.exception.DNSException:
            return None
    except dns.exception.DNSException:
        log.warning("No se pudo consultar el DNS de %s; se acepta y se confía en el enlace de confirmación", dominio)
        return None


def validar(email: str) -> CorreoValidado:
    """Devuelve el correo normalizado o lanza CorreoNoValido con un mensaje para la persona."""
    texto = (email or "").strip()
    try:
        info = validate_email(texto, check_deliverability=False)
    except EmailNotValidError as error:
        raise CorreoNoValido("El correo no tiene un formato válido.") from error

    local, dominio = info.local_part, info.domain.lower()
    normalizado = f"{local}@{dominio}".lower()

    # Primero el tipeo: varios dominios mal escritos («gmial.com») están en la lista de desechables.
    sugerido = sugerir_dominio(dominio)
    if sugerido:
        sugerencia = f"{local.lower()}@{sugerido}"
        raise CorreoNoValido(f"Revisa el correo: ¿quisiste decir {sugerencia}?", sugerencia)

    if any(d in DESECHABLES for d in (dominio, *_padres(dominio))):
        raise CorreoNoValido("No se aceptan correos temporales o desechables. Usa tu correo personal o institucional.")

    if get_settings().verificar_dns_correo and dominio_recibe_correo(dominio) is False:
        raise CorreoNoValido(f"El dominio «{dominio}» no existe o no recibe correos. Revisa que esté bien escrito.")

    return CorreoValidado(email=normalizado, dominio=dominio)


def _padres(dominio: str) -> list[str]:
    """«a.b.mailinator.com» → ["b.mailinator.com", "mailinator.com"] (subdominios de servicios desechables)."""
    partes = dominio.split(".")
    return [".".join(partes[i:]) for i in range(1, len(partes) - 1)]
