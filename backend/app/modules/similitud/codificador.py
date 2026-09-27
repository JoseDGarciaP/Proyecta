"""Convierte textos en vectores con sentence-transformers.

El modelo se carga una sola vez y solo cuando se necesita. Si la librería no está instalada
o el modelo no se puede descargar, `obtener()` devuelve None y el sistema usa similitud léxica.
"""

import logging
import threading
from typing import Protocol

from app.core.config import get_settings

log = logging.getLogger(__name__)


class Codificador(Protocol):
    nombre: str

    def codificar(self, textos: list[str]) -> list[list[float]]:
        """Vectores normalizados (norma 1), uno por texto."""
        ...


class SentenceTransformers:
    def __init__(self, nombre: str):
        from sentence_transformers import SentenceTransformer  # import pesado: solo al usarlo

        self.nombre = nombre
        self._modelo = SentenceTransformer(nombre, device="cpu")

    def codificar(self, textos: list[str]) -> list[list[float]]:
        return self._modelo.encode(textos, normalize_embeddings=True, convert_to_numpy=True).tolist()


_cargado: Codificador | None = None
_fallo: str | None = None
_candado = threading.Lock()

# Las pruebas asignan aquí un codificador falso para no descargar el modelo.
reemplazo: Codificador | None = None


def obtener() -> Codificador | None:
    global _cargado, _fallo
    if reemplazo is not None:
        return reemplazo
    settings = get_settings()
    if not settings.embeddings_activos:
        return None
    with _candado:
        if _cargado is None and _fallo is None:
            try:
                log.info("Cargando modelo de embeddings %s…", settings.embeddings_modelo)
                _cargado = SentenceTransformers(settings.embeddings_modelo)
            except Exception as error:  # ImportError, sin red, modelo inexistente…
                _fallo = f"{type(error).__name__}: {error}"
                log.warning("Sin embeddings, se usará similitud léxica (%s)", _fallo)
    return _cargado


def estado() -> dict:
    settings = get_settings()
    return {
        "activos": settings.embeddings_activos,
        "modelo": settings.embeddings_modelo,
        "cargado": _cargado is not None or reemplazo is not None,
        "error": _fallo,
    }
