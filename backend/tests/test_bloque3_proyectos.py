"""Bloque 3: problema y objetivos, varias áreas, historial de cambios, archivar, adjuntos y observaciones."""

import io
import zipfile

from tests.conftest import APRUEBA, RECO, registrar
from tests.test_proyectos import PROYECTO


def _crear(client, headers, **extra):
    res = client.post("/api/proyectos", json={**PROYECTO, **extra}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def _con_miembro(client, estudiante):
    pid = _crear(client, estudiante)["id"]
    luis = registrar(client, "luis@ufpso.edu.co", "Luis Rojas")
    sol = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()
    assert client.post(f"/api/alianzas/{sol['id']}/aceptar", json=APRUEBA, headers=estudiante).status_code == 200
    return pid, luis


def test_problema_objetivos_y_varias_areas(client, estudiante):
    p = _crear(client, estudiante, problema="Pérdidas por riego", objetivos="Reducir el agua 30 %",
               areas_extra=["Tecnología", "Agroindustria"])
    assert p["problema"] == "Pérdidas por riego" and p["objetivos"] == "Reducir el agua 30 %"
    assert p["areas"] == ["Agroindustria", "Tecnología"]
    ids = [x["id"] for x in client.get("/api/proyectos?area=Tecnología", headers=estudiante).json()]
    assert p["id"] in ids


def test_historial_y_aviso_al_equipo(client, estudiante):
    pid, luis = _con_miembro(client, estudiante)
    res = client.patch(f"/api/proyectos/{pid}", json={"estado": "finalizado", "avance": 100}, headers=estudiante)
    assert res.status_code == 200
    cambios = client.get(f"/api/proyectos/{pid}/cambios", headers=luis).json()
    assert cambios[0]["autor"] == "Ana Pérez"
    campos = {c["campo"]: c for c in cambios[0]["cambios"]}
    assert campos["Estado"]["antes"] == "ejecucion" and campos["Estado"]["despues"] == "finalizado"
    avisos = client.get("/api/notificaciones", headers=luis).json()
    assert any("Ana Pérez actualizó" in a["titulo"] and "Estado" in a["cuerpo"] for a in avisos)


def test_eliminar_sin_equipo_borra_y_queda_en_bitacora(client, estudiante, admin):
    pid = _crear(client, estudiante)["id"]
    res = client.request("DELETE", f"/api/proyectos/{pid}", json={"motivo": "Registro duplicado"}, headers=estudiante)
    assert res.status_code == 204
    assert client.get(f"/api/proyectos/{pid}", headers=estudiante).status_code == 404
    bitacora = client.get("/api/admin/registro", headers=admin).json()
    assert any(r["accion"] == "proyecto.eliminar" and "Registro duplicado" in r["detalle"] for r in bitacora)


def test_eliminar_con_equipo_archiva_y_avisa(client, estudiante):
    pid, luis = _con_miembro(client, estudiante)
    res = client.request("DELETE", f"/api/proyectos/{pid}", json={"motivo": "Se cerró la convocatoria"}, headers=estudiante)
    assert res.status_code == 204
    p = client.get(f"/api/proyectos/{pid}", headers=estudiante).json()
    assert p["archivado"] is True
    assert pid not in [x["id"] for x in client.get("/api/proyectos", headers=estudiante).json()]
    assert any("archivó" in a["titulo"] for a in client.get("/api/notificaciones", headers=luis).json())


def _docx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", "<document/>")
    return buf.getvalue()


def test_adjuntos(client, estudiante, tmp_path, monkeypatch):
    from app.core.config import get_settings
    monkeypatch.setattr(get_settings(), "archivos_dir", str(tmp_path))
    pid = _crear(client, estudiante)["id"]
    res = client.post(f"/api/proyectos/{pid}/adjuntos", headers=estudiante,
                      files={"archivo": ("propuesta.pdf", b"%PDF-1.4 contenido", "application/pdf")})
    assert res.status_code == 201, res.text
    adj = res.json()
    res = client.post(f"/api/proyectos/{pid}/adjuntos", headers=estudiante,
                      files={"archivo": ("acta.docx", _docx(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert res.status_code == 201, res.text
    assert client.post(f"/api/proyectos/{pid}/adjuntos", headers=estudiante,
                       files={"archivo": ("virus.exe", b"MZ...", "application/x-msdownload")}).status_code == 415
    otro = registrar(client, "luis@ufpso.edu.co", "Luis Rojas")
    assert client.post(f"/api/proyectos/{pid}/adjuntos", headers=otro,
                       files={"archivo": ("x.pdf", b"%PDF-1.4", "application/pdf")}).status_code == 403
    assert len(client.get(f"/api/proyectos/{pid}/adjuntos", headers=otro).json()) == 2
    assert client.get(f"/api/adjuntos/{adj['id']}/archivo", headers=otro).content.startswith(b"%PDF")
    assert client.delete(f"/api/adjuntos/{adj['id']}", headers=otro).status_code == 403
    assert client.delete(f"/api/adjuntos/{adj['id']}", headers=estudiante).status_code == 204


def test_observaciones(client, estudiante, admin):
    pid = _crear(client, estudiante)["id"]
    luis = registrar(client, "luis@ufpso.edu.co", "Luis Rojas")
    res = client.post(f"/api/proyectos/{pid}/observaciones", json={"texto": "¿Ya probaron con sensores capacitivos?"}, headers=luis)
    assert res.status_code == 201
    obs = res.json()
    # El dueño recibe aviso
    assert any("Nueva observación" in a["titulo"] for a in client.get("/api/notificaciones", headers=estudiante).json())
    # Solo el autor edita
    assert client.patch(f"/api/observaciones/{obs['id']}", json={"texto": "otro"}, headers=estudiante).status_code == 403
    assert client.patch(f"/api/observaciones/{obs['id']}", json={"texto": "¿Y sensores resistivos?"}, headers=luis).json()["editado_en"]
    # El admin la oculta con motivo y la restaura
    assert client.post(f"/api/admin/observaciones/{obs['id']}/ocultar", json={"motivo": "Lenguaje inapropiado"}, headers=admin).status_code == 200
    assert client.get(f"/api/proyectos/{pid}/observaciones", headers=estudiante).json() == []
    assert any("ocultó" in a["titulo"] for a in client.get("/api/notificaciones", headers=luis).json())
    client.post(f"/api/admin/observaciones/{obs['id']}/restaurar", headers=admin)
    assert len(client.get(f"/api/proyectos/{pid}/observaciones", headers=estudiante).json()) == 1
    assert client.delete(f"/api/observaciones/{obs['id']}", headers=luis).status_code == 204
