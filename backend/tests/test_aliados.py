"""Aliados externos: registro pendiente, aprobación o rechazo por un admin, perfil y directorio (Ep4-Hu12 a Hu15)."""

from tests.conftest import auth, token_del_correo

DATOS = {"email": "contacto@empresa.com", "password": "Clave-Segura1", "acepta_datos": True, "nombre": "Laura Gómez", "rol": "aliado",
         "aliado": {"razon_social": "Agro Norte SAS", "tipo": "Empresa", "documento": "900123456-1",
                    "telefono": "3001234567", "sector": "Agroindustria"}}


def _registrar_aliado(client, **cambios):
    res = client.post("/api/auth/registro", json={**DATOS, **cambios})
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_aliado_queda_pendiente_hasta_aprobacion(client, admin):
    usuario_id = _registrar_aliado(client)
    # Confirmar el correo no basta: sigue pendiente
    res = client.post("/api/auth/verificar", json={"token": token_del_correo("contacto@empresa.com")})
    assert res.status_code == 403 and "pendiente" in res.json()["detail"]
    res = client.post("/api/auth/login", data={"username": "contacto@empresa.com", "password": "Clave-Segura1"})
    assert res.status_code == 403 and "pendiente" in res.json()["detail"]

    pendientes = client.get("/api/admin/aliados?estado=pendiente", headers=admin).json()
    assert [p["razon_social"] for p in pendientes] == ["Agro Norte SAS"]
    assert client.post(f"/api/admin/aliados/{usuario_id}/aprobar", headers=admin).status_code == 200

    aliado = auth(client, "contacto@empresa.com")
    avisos = client.get("/api/notificaciones", headers=aliado).json()
    assert any("aprobada" in a["titulo"] for a in avisos)
    bitacora = client.get("/api/admin/registro", headers=admin).json()
    assert any(r["accion"] == "aliado.aprobar" for r in bitacora)


def test_rechazo_exige_motivo_y_lo_comunica(client, admin):
    usuario_id = _registrar_aliado(client)
    client.post("/api/auth/verificar", json={"token": token_del_correo("contacto@empresa.com")})
    assert client.post(f"/api/admin/aliados/{usuario_id}/rechazar", json={"motivo": ""}, headers=admin).status_code == 422
    res = client.post(f"/api/admin/aliados/{usuario_id}/rechazar", json={"motivo": "El NIT no corresponde"}, headers=admin)
    assert res.status_code == 200 and res.json()["estado"] == "rechazado"
    res = client.post("/api/auth/login", data={"username": "contacto@empresa.com", "password": "Clave-Segura1"})
    assert res.status_code == 403 and "El NIT no corresponde" in res.json()["detail"]
    from app.core import correo
    assert any("El NIT no corresponde" in c.texto for c in correo.enviados if c.para == "contacto@empresa.com")


def test_documento_unico(client):
    _registrar_aliado(client)
    res = client.post("/api/auth/registro", json={**DATOS, "email": "otra@empresa.com"})
    assert res.status_code == 409 and "NIT" in res.json()["detail"]


def test_aliado_edita_su_perfil_pero_no_el_documento(client, admin):
    usuario_id = _registrar_aliado(client)
    client.post("/api/auth/verificar", json={"token": token_del_correo("contacto@empresa.com")})
    client.post(f"/api/admin/aliados/{usuario_id}/aprobar", headers=admin)
    aliado = auth(client, "contacto@empresa.com")
    res = client.put("/api/aliados/yo", headers=aliado, json={"telefono": "3109998888", "sitio_web": "https://agronorte.co",
                                                              "documento": "111"})
    assert res.status_code == 200
    assert res.json()["telefono"] == "3109998888" and res.json()["documento"] == "900123456-1"
    res = client.put(f"/api/admin/aliados/{usuario_id}/documento", json={"documento": "900123456-2"}, headers=admin)
    assert res.json()["documento"] == "900123456-2"


def test_directorio_solo_muestra_aprobados(client, admin, estudiante):
    uno = _registrar_aliado(client)
    _registrar_aliado(client, email="dos@empresa.com", aliado={**DATOS["aliado"], "documento": "800555", "razon_social": "Otra",
                                                              "sector": "Salud"})
    client.post(f"/api/admin/aliados/{uno}/aprobar", headers=admin)
    nombres = [a["razon_social"] for a in client.get("/api/aliados", headers=estudiante).json()]
    assert nombres == ["Agro Norte SAS"]
    assert client.get("/api/aliados?sector=salud", headers=estudiante).json() == []
    assert len(client.get("/api/aliados?sector=agro", headers=estudiante).json()) == 1
