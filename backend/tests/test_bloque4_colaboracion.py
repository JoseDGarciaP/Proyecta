"""Bloque 4: aceptar y anular recomendaciones, pesos, valoración del diagnóstico, roles, anulación, transferencia y aportes."""

from datetime import date, timedelta

from tests.conftest import registrar
from tests.test_bloque3_proyectos import _con_miembro, _crear
from tests.test_ia import _oportunidad
from tests.test_proyectos import PROYECTO


def test_aceptar_y_anular_recomendacion(client, estudiante, admin):
    a = _oportunidad(admin, client, titulo="Fondo agroindustrial A")
    b = _oportunidad(admin, client, titulo="Fondo agroindustrial B")
    pid = _crear(client, estudiante)["id"]
    recs = {r["oportunidad_id"]: r for r in client.post(f"/api/ia/proyectos/{pid}/analisis", headers=estudiante).json()["recomendaciones"]}

    ok = client.post(f"/api/ia/recomendaciones/{recs[a['id']]['recomendacion_id']}/aceptar", headers=estudiante)
    assert ok.status_code == 200 and ok.json()["estado"] == "aceptada"
    assert client.post(f"/api/ia/recomendaciones/{recs[a['id']]['recomendacion_id']}/aceptar", headers=estudiante).status_code == 409

    rid = recs[b["id"]]["recomendacion_id"]
    assert client.post(f"/api/ia/recomendaciones/{rid}/anular", json={"motivo": "no"}, headers=estudiante).status_code == 422
    extrano = registrar(client, "otro@ufpso.edu.co", "Otro")
    assert client.post(f"/api/ia/recomendaciones/{rid}/anular", json={"motivo": "No aplica a nosotros"}, headers=extrano).status_code == 403
    res = client.post(f"/api/ia/recomendaciones/{rid}/anular", json={"motivo": "No aplica a nosotros"}, headers=estudiante)
    assert res.status_code == 200 and res.json()["motivo"] == "No aplica a nosotros"

    nuevas = client.post(f"/api/ia/proyectos/{pid}/analisis", headers=estudiante).json()["recomendaciones"]
    assert b["id"] not in [r["oportunidad_id"] for r in nuevas]


def test_peso_habilidades_ajustable(client, estudiante):
    pid = _crear(client, estudiante)["id"]
    assert client.get(f"/api/ia/proyectos/{pid}/colaboradores?peso_habilidades=0.8", headers=estudiante).status_code == 200
    assert client.get(f"/api/ia/proyectos/{pid}/colaboradores?peso_habilidades=2", headers=estudiante).status_code == 422


def test_diagnostico_cita_similares_y_se_valora(client, estudiante):
    pid = _crear(client, estudiante)["id"]
    _crear(client, estudiante, titulo="Riego inteligente para cacao")
    cuerpo = client.post(f"/api/ia/proyectos/{pid}/analisis", headers=estudiante).json()
    assert "similares" in cuerpo
    res = client.post(f"/api/ia/proyectos/{pid}/diagnostico/valoracion", json={"util": True}, headers=estudiante)
    assert res.status_code == 201 and res.json() == {"utiles": 1, "no_utiles": 0, "mia": True}
    res = client.post(f"/api/ia/proyectos/{pid}/diagnostico/valoracion", json={"util": False, "comentario": "Muy general"}, headers=estudiante)
    assert res.json() == {"utiles": 0, "no_utiles": 1, "mia": False}


def test_cambiar_rol_queda_en_historial(client, estudiante):
    pid, luis = _con_miembro(client, estudiante)
    luis_id = client.get("/api/usuarios/yo", headers=luis).json()["id"]
    assert client.patch(f"/api/proyectos/{pid}/miembros/{luis_id}", json={"rol": "Tesorero"}, headers=luis).status_code == 403
    res = client.patch(f"/api/proyectos/{pid}/miembros/{luis_id}", json={"rol": "Tesorero"}, headers=estudiante)
    assert res.status_code == 200 and res.json()["rol"] == "Tesorero"
    cambios = client.get(f"/api/proyectos/{pid}/cambios", headers=estudiante).json()
    assert cambios[0]["cambios"][0]["campo"] == "Rol de Luis Rojas"
    assert any("Tu rol" in n["titulo"] for n in client.get("/api/notificaciones", headers=luis).json())


def test_anular_alianza_con_motivo(client, estudiante):
    pid, luis = _con_miembro(client, estudiante)
    luis_id = client.get("/api/usuarios/yo", headers=luis).json()["id"]
    res = client.request("DELETE", f"/api/proyectos/{pid}/miembros/{luis_id}", json={"motivo": "Cambio de semestre"}, headers=estudiante)
    assert res.status_code == 204
    historial = client.get("/api/alianzas", headers=luis).json()
    assert historial[0]["estado"] == "anulada" and historial[0]["respuesta"] == "Cambio de semestre"
    assert any("Ya no haces parte" in n["titulo"] for n in client.get("/api/notificaciones", headers=luis).json())


def test_transferir_propiedad(client, estudiante):
    pid, luis = _con_miembro(client, estudiante)
    yo = client.get("/api/usuarios/yo", headers=estudiante).json()["id"]
    luis_id = client.get("/api/usuarios/yo", headers=luis).json()["id"]
    assert client.post(f"/api/proyectos/{pid}/transferir", json={"usuario_id": yo}, headers=luis).status_code == 403
    assert client.post(f"/api/proyectos/{pid}/transferir", json={"usuario_id": luis_id}, headers=estudiante).status_code == 204
    p = client.get(f"/api/proyectos/{pid}", headers=estudiante).json()
    assert p["creado_por"] == luis_id and p["lider"] == "Luis Rojas"
    miembros = [m["usuario_id"] for m in client.get(f"/api/proyectos/{pid}/miembros", headers=luis).json()]
    assert miembros == [yo]
    # El antiguo dueño ya puede salir del proyecto.
    assert client.request("DELETE", f"/api/proyectos/{pid}/miembros/{yo}", json={"motivo": "Me gradúo"}, headers=estudiante).status_code == 204


def test_registro_y_validacion_de_aportes(client, estudiante):
    pid, luis = _con_miembro(client, estudiante)
    extrano = registrar(client, "otro@ufpso.edu.co", "Otro")
    aporte = {"tipo": "Horas de trabajo", "descripcion": "Instalé los sensores", "horas": 6, "fecha": str(date.today())}
    assert client.post(f"/api/proyectos/{pid}/aportes", json=aporte, headers=extrano).status_code == 403
    futuro = {**aporte, "fecha": str(date.today() + timedelta(days=3))}
    assert client.post(f"/api/proyectos/{pid}/aportes", json=futuro, headers=luis).status_code == 422
    a = client.post(f"/api/proyectos/{pid}/aportes", json=aporte, headers=luis).json()
    assert a["estado"] == "pendiente"
    assert client.get(f"/api/proyectos/{pid}/aportes", headers=extrano).json()["aportes"] == []

    assert client.post(f"/api/aportes/{a['id']}/validar", json={}, headers=luis).status_code == 403
    assert client.post(f"/api/aportes/{a['id']}/rechazar", json={"comentario": ""}, headers=estudiante).status_code == 422
    assert client.post(f"/api/aportes/{a['id']}/validar", json={"comentario": "Gracias"}, headers=estudiante).json()["estado"] == "validado"
    resumen = client.get(f"/api/proyectos/{pid}/aportes", headers=extrano).json()
    assert resumen["horas_validadas"] == 6 and len(resumen["aportes"]) == 1
    assert any("fue validado" in n["titulo"] for n in client.get("/api/notificaciones", headers=luis).json())
