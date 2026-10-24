"""Envía el resumen de mensajes sin leer (lo mismo que hace la API cada pocos minutos).

Uso: python -m scripts.enviar_resumenes   (útil con RESUMEN_AUTOMATICO=false y un cron)
"""

from app.core.database import SessionLocal
from app.modules.notificaciones.servicio import enviar_resumenes


def main() -> None:
    with SessionLocal() as db:
        print(f"Avisos enviados: {enviar_resumenes(db)}")


if __name__ == "__main__":
    main()
