"""Descarga el modelo de embeddings (si falta) y calcula los vectores de todo lo registrado.

No es obligatorio: la API calcula los vectores que faltan la primera vez que los necesita.
Sirve para comprobar que sentence-transformers funciona y para que la primera búsqueda sea rápida.

Uso: python -m scripts.indexar_embeddings
"""

import sys
import time

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Oportunidad, Proyecto, Usuario
from app.modules.similitud import codificador, textos
from app.modules.similitud.servicio import asegurar


def main() -> None:
    inicio = time.perf_counter()
    cod = codificador.obtener()
    if cod is None:
        sys.exit(f"No se pudo cargar el modelo: {codificador.estado()['error'] or 'EMBEDDINGS_ACTIVOS=false'}")
    print(f"Modelo {cod.nombre} listo en {time.perf_counter() - inicio:.1f} s")
    with SessionLocal() as db:
        for entidad, modelo, texto in (
            ("proyecto", Proyecto, textos.proyecto),
            ("oportunidad", Oportunidad, textos.oportunidad),
            ("usuario", Usuario, textos.usuario),
        ):
            objetos = [o for o in db.scalars(select(modelo)).unique() if texto(o)]
            asegurar(db, entidad, objetos, texto, cod)
            print(f"  {entidad}: {len(objetos)} vectores al día")
    print(f"Listo en {time.perf_counter() - inicio:.1f} s")


if __name__ == "__main__":
    main()
