"""Bloque 6: historial personal, bitácora con filtros, ocultar y restaurar proyectos, estadísticas y Excel del panel."""

import io
from datetime import date, timedelta

from openpyxl import load_workbook

from tests.test_bloque3_proyectos import _con_miembro, _crear
from tests.test_ia import _oportunidad


def test_historial_personal_filtra_y_exporta(client, estudiante):
    pid, luis = _con_miembro(client, estudiante)
    todo = client.get("/api/usuarios/yo/historial", headers=luis).json()
    assert {"alianza", "logro"} <= {e["tipo"] for e in todo}
    solo = client.get("/api/usuarios/yo/historial?tipo=alianza", headers=luis).json()
    assert solo and all(e["tipo"] == "alianza" for e in solo)
    assert client.get(f"/api/usuarios/yo/historial?anio={date.today().year - 3}", headers=luis).json() == []
    proyectos = client.get("/api/usuarios/yo/historial?tipo=proyecto", headers=estudiante).json()
    assert proyectos[0]["enlace"] == f"/proyectos/{pid}"
    res = client.get("/api/usuarios/yo/historial.xlsx", headers=luis)
    ws = load_workbook(io.BytesIO(res.content)).active
    assert "Luis Rojas" in ws["A1"].value and ws["B3"].value == "Tipo"


def test_ocultar_y_restaurar_proyecto(client, admin, estudiante):
    pid = _crear(client, estudiante)["id"]
    assert client.post(f"/api/admin/proyectos/{pid}/ocultar", json={"motivo": "Contenido duplicado"}, headers=admin).status_code == 204
    assert pid not in [p["id"] for p in client.get("/api/proyectos", headers=estudiante).json()]
    fila = next(p for p in client.get("/api/admin/proyectos", headers=admin).json() if p["id"] == pid)
    assert fila["archivado"] is True and "Contenido duplicado" in fila["archivado_motivo"]
    assert client.post(f"/api/admin/proyectos/{pid}/restaurar", headers=admin).status_code == 204
    assert pid in [p["id"] for p in client.get("/api/proyectos", headers=estudiante).json()]
    avisos = [a["titulo"] for a in client.get("/api/notificaciones", headers=estudiante).json()]
    assert any("Se ocultó" in t for t in avisos) and any("Se restauró" in t for t in avisos)


def test_bitacora_filtra_por_persona_y_fecha(client, admin, estudiante):
    pid = _crear(client, estudiante)["id"]
    client.post(f"/api/admin/proyectos/{pid}/ocultar", json={"motivo": "Contenido duplicado"}, headers=admin)
    hoy = date.today()
    assert client.get("/api/admin/registro?usuario=Admin", headers=admin).json()
    assert client.get("/api/admin/registro?usuario=nadie-asi", headers=admin).json() == []
    assert client.get(f"/api/admin/registro?desde={hoy}&hasta={hoy}", headers=admin).json()
    assert client.get(f"/api/admin/registro?hasta={hoy - timedelta(days=2)}", headers=admin).json() == []


def test_estadisticas_detalle_y_excel(client, admin, estudiante):
    _crear(client, estudiante)
    op = _oportunidad(admin, client)
    pid = _crear(client, estudiante, titulo="Otro proyecto")["id"]
    recs = client.post(f"/api/ia/proyectos/{pid}/analisis", headers=estudiante).json()["recomendaciones"]
    client.post(f"/api/ia/recomendaciones/{recs[0]['recomendacion_id']}/aceptar", headers=estudiante)
    post = client.post(f"/api/oportunidades/{op['id']}/postulaciones",
                       json={"proyecto_id": pid, "nota": "Encaja con la línea de agua del fondo."}, headers=estudiante).json()
    client.patch(f"/api/admin/postulaciones/{post['id']}", json={"estado": "aceptada", "comentario": "Bien"}, headers=admin)

    d = client.get("/api/admin/estadisticas/detalle", headers=admin).json()
    assert d["proyectos"] == 2 and d["por_programa"][0]["total"] == 2
    assert d["tasa_exito_postulaciones"] == 1.0
    assert d["recomendaciones_generadas"] >= 1 and d["recomendaciones_aceptadas"] == 1
    assert d["por_mes"][-1]["proyectos"] == 2
    manana = date.today() + timedelta(days=1)
    assert client.get(f"/api/admin/estadisticas/detalle?desde={manana}", headers=admin).json()["proyectos"] == 0
    assert client.get("/api/admin/estadisticas/detalle", headers=estudiante).status_code == 403

    res = client.get("/api/admin/reporte.xlsx", headers=admin)
    libro = load_workbook(io.BytesIO(res.content))
    assert {"Resumen", "Por programa", "Por mes", "Proyectos"} <= set(libro.sheetnames)
    assert "generado el" in libro["Resumen"]["A1"].value
