"""Bloque 5: archivar convocatorias con postulaciones, avisar cambios de fecha y cierres, archivar notificaciones y exportar."""

import io
from datetime import date, timedelta

from openpyxl import load_workbook

from app.modules.notificaciones.models import Notificacion
from app.modules.oportunidades.avisos import archivar_notificaciones, avisar_cierres
from tests.test_bloque3_proyectos import _crear
from tests.test_ia import _oportunidad


def _postular(client, estudiante, oid):
    pid = _crear(client, estudiante)["id"]
    res = client.post(f"/api/oportunidades/{oid}/postulaciones",
                      json={"proyecto_id": pid, "nota": "Nuestro piloto encaja con la línea de agua."}, headers=estudiante)
    assert res.status_code == 201, res.text
    return pid


def _avisos(client, quien):
    return client.get("/api/notificaciones", headers=quien).json()


def test_cambio_de_fechas_avisa_a_postulantes(client, admin, estudiante):
    op = _oportunidad(admin, client)
    _postular(client, estudiante, op["id"])
    datos = {k: op[k] for k in ("titulo", "entidad", "tipo", "descripcion", "monto", "abre_en", "url")}
    datos |= {"areas": op["areas"], "ods": op["ods"], "cierra_en": str(date.today() + timedelta(days=40))}
    assert client.put(f"/api/oportunidades/{op['id']}", json=datos, headers=admin).status_code == 200
    assert any(a["tipo"] == "convocatoria" and "Cambiaron las fechas" in a["titulo"] for a in _avisos(client, estudiante))


def test_eliminar_con_postulaciones_archiva(client, admin, estudiante):
    op = _oportunidad(admin, client)
    _postular(client, estudiante, op["id"])
    res = client.request("DELETE", f"/api/oportunidades/{op['id']}", json={"motivo": "Se canceló el fondo"}, headers=admin)
    assert res.status_code == 204
    assert op["id"] not in [o["id"] for o in client.get("/api/oportunidades", headers=admin).json()]
    assert op["id"] in [o["id"] for o in client.get("/api/oportunidades?archivadas=true", headers=admin).json()]
    assert any("Se archivó la convocatoria" in a["titulo"] for a in _avisos(client, estudiante))
    assert client.post(f"/api/oportunidades/{op['id']}/restaurar", headers=admin).status_code == 200
    sola = _oportunidad(admin, client, titulo="Sin postulaciones")
    assert client.request("DELETE", f"/api/oportunidades/{sola['id']}", headers=admin).status_code == 204
    assert client.get(f"/api/oportunidades/{sola['id']}", headers=admin).status_code == 404


def test_avisos_de_cierre_una_sola_vez(client, admin, estudiante, db):
    op = _oportunidad(admin, client, cierra_en=str(date.today() + timedelta(days=6)))
    pid = _crear(client, estudiante)["id"]
    client.post(f"/api/ia/proyectos/{pid}/analisis", headers=estudiante)  # queda recomendada
    assert avisar_cierres(db) == 1
    assert avisar_cierres(db) == 0  # no se repite
    assert any("cierra en 6 días" in a["titulo"] for a in _avisos(client, estudiante))
    assert avisar_cierres(db, hoy=date.today() + timedelta(days=5)) == 1
    assert any("cierra mañana" in a["titulo"] for a in _avisos(client, estudiante))
    assert op["id"]


def test_notificaciones_viejas_se_archivan(client, estudiante, db):
    from app.core.database import utcnow

    _crear(client, estudiante)  # genera al menos un aviso (XP/insignia)
    total = len(_avisos(client, estudiante))
    assert total > 0
    for n in db.query(Notificacion).all():
        n.creada_en = utcnow() - timedelta(days=120)
    db.commit()
    assert archivar_notificaciones(db) >= total
    assert _avisos(client, estudiante) == []
    archivadas = client.get("/api/notificaciones?archivadas=true", headers=estudiante).json()
    assert len(archivadas) == total
    nid = archivadas[0]["id"]
    assert client.post(f"/api/notificaciones/{nid}/archivar?deshacer=true", headers=estudiante).json()["archivada"] is False


def test_exportar_participaciones_excel(client, admin, estudiante):
    op = _oportunidad(admin, client)
    _postular(client, estudiante, op["id"])
    res = client.get("/api/admin/postulaciones/exportar.xlsx", headers=admin)
    assert res.status_code == 200 and "spreadsheetml" in res.headers["content-type"]
    ws = load_workbook(io.BytesIO(res.content)).active
    assert "generado el" in ws["A1"].value
    assert ws["A3"].value == "Convocatoria" and ws["A4"].value == "Fondo agroindustrial"
    assert client.get("/api/admin/postulaciones/exportar.xlsx", headers=estudiante).status_code == 403
