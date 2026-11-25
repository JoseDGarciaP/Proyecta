from contextlib import contextmanager
from datetime import date

from sqlalchemy import func, select

from app.models import Actor, Oportunidad
from scripts import cargar_datos_demo as demo


def _usar(monkeypatch, db):
    @contextmanager
    def sesion():
        yield db
    monkeypatch.setattr(demo, "SessionLocal", sesion)


def _contar(db, modelo):
    return db.scalar(select(func.count()).select_from(modelo))


def test_carga_sin_duplicar_y_abiertas(monkeypatch, db):
    _usar(monkeypatch, db)
    base = Oportunidad(titulo="Fondo de innovación agroindustrial", entidad="Cámara", tipo="financiacion",
                       cierra_en=date(2026, 1, 1))
    db.add(base)
    db.commit()

    demo.cargar()
    actores, oportunidades = _contar(db, Actor), _contar(db, Oportunidad)
    assert actores == len(demo.EXTRA["actores"])
    assert oportunidades == len(demo.EXTRA["oportunidades"]) + 1
    assert base.descripcion  # se completó la descripción vacía
    nuevas = db.scalars(select(Oportunidad).where(Oportunidad.id != base.id)).all()
    assert all(o.cierra_en > date.today() and o.descripcion and o.areas and o.ods for o in nuevas)

    demo.cargar()  # segunda vez: no duplica
    assert (_contar(db, Actor), _contar(db, Oportunidad)) == (actores, oportunidades)


def test_borrar_solo_lo_de_demo(monkeypatch, db):
    _usar(monkeypatch, db)
    real = Actor(nombre="Aliado real", tipo="empresa")
    db.add(real)
    db.commit()
    demo.cargar()
    demo.borrar()
    assert db.scalars(select(Actor)).all() == [real]
    assert _contar(db, Oportunidad) == 0


def test_informe_de_similitud(monkeypatch, db, client, estudiante, capsys):
    from scripts import evaluar_similitud as informe
    from tests.test_proyectos import PROYECTO

    _usar(monkeypatch, db)
    monkeypatch.setattr(informe, "SessionLocal", demo.SessionLocal)
    demo.cargar()
    assert client.post("/api/proyectos", json=PROYECTO, headers=estudiante).status_code == 201
    informe.main()
    salida = capsys.readouterr().out
    assert "Oportunidades:" in salida and "Distribución de puntajes" in salida
