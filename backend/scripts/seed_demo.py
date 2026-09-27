"""Carga los datos de ejemplo de la maqueta (los mismos de src/data/mock.ts) en la base de datos.

Uso: python -m scripts.seed_demo
Solo carga si no hay proyectos todavía. Los proyectos quedan sin autor (creado_por vacío).
"""

import json
from datetime import date
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import Actor, Oportunidad, Proyecto
from app.modules.catalogo.service import area_por_nombre, areas_por_nombre, ods_por_id

DATOS = json.loads((Path(__file__).parent / "datos_demo.json").read_text(encoding="utf-8"))

# ODS sugeridos por área para que la recomendación tenga con qué trabajar
ODS_POR_AREA = {
    "Tecnología": [9], "Ambiente": [11, 13], "Salud": [3], "Educación": [4],
    "Agroindustria": [2, 8], "Social": [8, 10], "Energía": [7],
}


def main() -> None:
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(Proyecto)):
            print("Ya hay proyectos; no se cargan datos de ejemplo.")
            return

        actores = {}
        for a in DATOS["actores"]:
            actores[a["id"]] = Actor(nombre=a["nombre"], tipo=a["tipo"], sector=a["sector"], contacto=a["contacto"])
        db.add_all(actores.values())

        for o in DATOS["oportunidades"]:
            op = Oportunidad(titulo=o["titulo"], entidad=o["entidad"], tipo=o["tipo"], monto=o["monto"],
                             cierra_en=date.fromisoformat(o["cierra_en"]), url=o["url"])
            op.areas = areas_por_nombre(db, o["areas"])
            op.ods = ods_por_id(db, sorted({n for a in o["areas"] for n in ODS_POR_AREA.get(a, [])}))
            db.add(op)

        for p in DATOS["proyectos"]:
            proyecto = Proyecto(
                titulo=p["titulo"], resumen=p["resumen"], descripcion=p["descripcion"], estado=p["estado"],
                avance=p["avance"], presupuesto=p["presupuesto"], lider=p["lider"], equipo=p["equipo"],
                etiquetas=p["etiquetas"], fecha_inicio=date.fromisoformat(p["fecha_inicio"]),
                fecha_fin=date.fromisoformat(p["fecha_fin"]) if p["fecha_fin"] else None,
                creado_en=date.fromisoformat(p["creado_en"]),
            )
            proyecto.area = area_por_nombre(db, p["area"])
            proyecto.ods = ods_por_id(db, ODS_POR_AREA.get(p["area"], []))
            proyecto.actores = [actores[i] for i in p["actores"]]
            db.add(proyecto)

        db.commit()
        print(f"Cargados {len(DATOS['proyectos'])} proyectos, {len(actores)} actores "
              f"y {len(DATOS['oportunidades'])} oportunidades.")


if __name__ == "__main__":
    main()
