"""Avisos de convocatorias por cerrar y archivo de notificaciones de más de 90 días.

Uso: python -m scripts.tarea_diaria   (útil con RESUMEN_AUTOMATICO=false y un cron diario)
"""

from app.core.database import SessionLocal
from app.modules.oportunidades.avisos import archivar_notificaciones, avisar_cierres


def main() -> None:
    with SessionLocal() as db:
        print(f"Avisos de cierre: {avisar_cierres(db)}")
        print(f"Notificaciones archivadas: {archivar_notificaciones(db)}")


if __name__ == "__main__":
    main()
