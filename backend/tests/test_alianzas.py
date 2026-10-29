from tests.conftest import APRUEBA, RECHAZA, RECO, registrar
from tests.test_proyectos import PROYECTO


def _proyecto(client, headers):
    res = client.post("/api/proyectos", json=PROYECTO, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _yo(client, headers):
    return client.get("/api/usuarios/yo", headers=headers).json()


def test_solicitar_y_aceptar_crea_miembro_e_historial(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")

    res = client.post(f"/api/proyectos/{pid}/solicitudes", json={**RECO, "mensaje": "Sé de sensores"}, headers=luis)
    assert res.status_code == 201, res.text
    solicitud = res.json()
    assert solicitud["estado"] == "pendiente" and solicitud["por_responder"] is False

    # Duplicada o respondida por quien no corresponde
    assert client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).status_code == 409
    assert client.post(f"/api/alianzas/{solicitud['id']}/aceptar", json=APRUEBA, headers=luis).status_code == 403

    pendientes = client.get("/api/alianzas", headers=estudiante).json()
    assert [s["por_responder"] for s in pendientes] == [True]

    res = client.post(f"/api/alianzas/{solicitud['id']}/aceptar", json={**APRUEBA, "respuesta": "¡Bienvenido!"}, headers=estudiante)
    assert res.json()["estado"] == "aceptada"
    assert [m["nombre"] for m in client.get(f"/api/proyectos/{pid}/miembros", headers=estudiante).json()] == ["Luis Gómez"]
    assert client.post(f"/api/alianzas/{solicitud['id']}/rechazar", json=RECHAZA, headers=estudiante).status_code == 409
    assert client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).status_code == 409  # ya es miembro

    perfil = client.get("/api/perfil", headers=luis).json()
    assert perfil["resumen"] == {"proyectos": 1, "colaboraciones": 1, "alianzas_activas": 1, "por_responder": 0}
    assert perfil["proyectos"][0]["mi_rol"] == "colaborador"
    assert perfil["alianzas"][0]["respuesta"] == "¡Bienvenido!"


def test_el_dueno_no_se_solicita_a_si_mismo(client, estudiante):
    pid = _proyecto(client, estudiante)
    assert client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=estudiante).status_code == 409


def test_invitacion_la_responde_el_invitado(client, estudiante):
    pid = _proyecto(client, estudiante)
    maria = registrar(client, "maria@ufpso.edu.co", nombre="María Ruiz")
    maria_id = _yo(client, maria)["id"]
    otro = registrar(client, "otro@ufpso.edu.co", nombre="Otro Usuario")

    assert client.post(f"/api/proyectos/{pid}/invitaciones", json={**RECO, "usuario_id": maria_id}, headers=otro).status_code == 403
    inv = client.post(f"/api/proyectos/{pid}/invitaciones", json={**RECO, "usuario_id": maria_id}, headers=estudiante).json()
    assert inv["tipo"] == "invitacion"
    assert client.post(f"/api/alianzas/{inv['id']}/aceptar", json=APRUEBA, headers=estudiante).status_code == 403

    assert client.post(f"/api/alianzas/{inv['id']}/rechazar", json=RECHAZA, headers=maria).json()["estado"] == "rechazada"
    assert client.get(f"/api/proyectos/{pid}/miembros", headers=estudiante).json() == []
    # Tras un rechazo se puede volver a invitar, y quien invita puede cancelar
    inv2 = client.post(f"/api/proyectos/{pid}/invitaciones", json={**RECO, "usuario_id": maria_id}, headers=estudiante).json()
    assert client.post(f"/api/alianzas/{inv2['id']}/cancelar", headers=maria).status_code == 403
    assert client.post(f"/api/alianzas/{inv2['id']}/cancelar", headers=estudiante).json()["estado"] == "cancelada"


def test_miembro_puede_retirarse(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    luis_id = _yo(client, luis)["id"]
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)

    intruso = registrar(client, "intruso@ufpso.edu.co", nombre="Intruso")
    assert client.delete(f"/api/proyectos/{pid}/miembros/{luis_id}", headers=intruso).status_code == 403
    assert client.delete(f"/api/proyectos/{pid}/miembros/{luis_id}", headers=luis).status_code == 204
    assert client.get("/api/perfil", headers=luis).json()["proyectos"] == []


def test_perfil_del_responsable(client, estudiante):
    _proyecto(client, estudiante)
    perfil = client.get("/api/perfil", headers=estudiante).json()
    assert perfil["usuario"]["email"] == "ana@ufpso.edu.co"
    assert perfil["proyectos"][0]["mi_rol"] == "responsable"
    assert perfil["resumen"]["proyectos"] == 1 and perfil["alianzas"] == []
    assert client.get("/api/perfil").status_code == 401


def test_solo_el_lider_edita_el_proyecto_no_los_colaboradores(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)

    # Ya es miembro del equipo, pero no puede cambiar la formulación
    cambio = {"titulo": "Título cambiado por otro", "descripcion": "otra cosa", "equipo": ["Luis"], "etiquetas": ["x"]}
    assert client.patch(f"/api/proyectos/{pid}", json=cambio, headers=luis).status_code == 403
    assert client.delete(f"/api/proyectos/{pid}", headers=luis).status_code == 403

    # El líder sí
    res = client.patch(f"/api/proyectos/{pid}", json=cambio, headers=estudiante)
    assert res.status_code == 200, res.text
    datos = res.json()
    assert datos["titulo"] == "Título cambiado por otro" and datos["equipo"] == ["Luis"] and datos["etiquetas"] == ["x"]
