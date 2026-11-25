"""Agrega actores y convocatorias de demostración sin tocar los datos reales.

Uso (en el servidor):
    docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec api python -m scripts.cargar_datos_demo
    ... exec api python -m scripts.cargar_datos_demo --borrar      # quita lo que este script agregó

A diferencia de seed_demo (que solo corre con la base vacía), este script:
- agrega los actores y oportunidades de datos_demo_extra.json que todavía no existan (por nombre o título);
  se puede correr varias veces sin duplicar nada;
- calcula las fechas a partir de hoy, así las convocatorias quedan abiertas el día de la demo;
- completa la descripción de las 10 oportunidades de datos_demo.json si están vacías (la IA compara textos:
  sin descripción solo tenía el título).

--borrar elimina los actores de demostración que no estén ligados a ningún proyecto y las oportunidades de
demostración sin postulaciones; las que ya tienen postulaciones se archivan para no perder nada.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import Actor, Oportunidad
from app.modules.actores.models import proyecto_actores
from app.modules.catalogo.service import areas_por_nombre, ods_por_id
from app.modules.postulaciones.models import Postulacion

EXTRA = json.loads((Path(__file__).parent / "datos_demo_extra.json").read_text(encoding="utf-8"))

ODS_POR_AREA = {
    "Tecnología": [9], "Ambiente": [6, 13, 15], "Salud": [3], "Educación": [4],
    "Agroindustria": [2, 8], "Social": [5, 10], "Energía": [7], "Seguridad": [16], "Seguridad vial": [3, 11],
}


def cargar() -> None:
    hoy = date.today()
    with SessionLocal() as db:
        existentes = set(db.scalars(select(Actor.nombre)))
        nuevos_actores = [Actor(nombre=a["nombre"], tipo=a["tipo"], sector=a["sector"], contacto=a["contacto"])
                          for a in EXTRA["actores"] if a["nombre"] not in existentes]
        db.add_all(nuevos_actores)

        titulos = set(db.scalars(select(Oportunidad.titulo)))
        nuevas = 0
        for o in EXTRA["oportunidades"]:
            if o["titulo"] in titulos:
                continue
            op = Oportunidad(titulo=o["titulo"], entidad=o["entidad"], tipo=o["tipo"], descripcion=o["descripcion"],
                             monto=o["monto"], url="https://ejemplo.gov.co/convocatoria",
                             abre_en=hoy - timedelta(days=o["abre_hace_dias"]),
                             cierra_en=hoy + timedelta(days=o["cierra_en_dias"]))
            op.areas = areas_por_nombre(db, o["areas"])
            op.ods = ods_por_id(db, sorted({n for a in o["areas"] for n in ODS_POR_AREA.get(a, [])}))
            db.add(op)
            nuevas += 1

        completadas = 0
        for titulo, descripcion in EXTRA["descripciones_base"].items():
            op = db.scalar(select(Oportunidad).where(Oportunidad.titulo == titulo))
            if op is not None and not (op.descripcion or "").strip():
                op.descripcion = descripcion
                completadas += 1

        db.commit()
        abiertas = db.scalar(select(func.count()).select_from(Oportunidad).where(
            Oportunidad.cierra_en >= hoy, Oportunidad.archivada.is_(False)))
        print(f"Agregados {len(nuevos_actores)} actores y {nuevas} oportunidades; "
              f"{completadas} descripciones completadas. Oportunidades abiertas ahora: {abiertas}.")


def borrar() -> None:
    with SessionLocal() as db:
        nombres = [a["nombre"] for a in EXTRA["actores"]]
        borrados = archivadas = conservados = 0
        for actor in db.scalars(select(Actor).where(Actor.nombre.in_(nombres))):
            usado = db.scalar(select(func.count()).select_from(proyecto_actores).where(
                proyecto_actores.c.actor_id == actor.id))
            if usado:
                conservados += 1
            else:
                db.delete(actor)
                borrados += 1

        titulos = [o["titulo"] for o in EXTRA["oportunidades"]]
        for op in db.scalars(select(Oportunidad).where(Oportunidad.titulo.in_(titulos))):
            if db.scalar(select(func.count()).select_from(Postulacion).where(Postulacion.oportunidad_id == op.id)):
                op.archivada = True
                archivadas += 1
            else:
                db.delete(op)
                borrados += 1
        db.commit()
        print(f"Borrados {borrados} registros de demostración; {archivadas} oportunidades archivadas por tener "
              f"postulaciones y {conservados} actores conservados por estar ligados a proyectos.")


if __name__ == "__main__":
    borrar() if "--borrar" in sys.argv else cargar()
