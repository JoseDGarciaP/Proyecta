from tests.conftest import registrar
from tests.test_alianzas import _proyecto, _yo


def _solicitud(client, responsable, mensaje="Me interesa el proyecto"):
    """Proyecto de `responsable` y una solicitud pendiente de Luis."""
    pid = _proyecto(client, responsable)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json={"mensaje": mensaje}, headers=luis).json()["id"]
    return pid, sid, luis


def test_conversan_antes_de_decidir(client, estudiante):
    _, sid, luis = _solicitud(client, estudiante)
    url = f"/api/alianzas/{sid}/mensajes"

    pregunta = client.post(url, json={"texto": "¿Qué experiencia tienes con sensores?"}, headers=estudiante)
    assert pregunta.status_code == 201, pregunta.text
    assert pregunta.json()["solicitud_id"] == sid and pregunta.json()["proyecto_id"] is None
    client.post(url, json={"texto": "Hice un proyecto con Arduino el semestre pasado"}, headers=luis)

    vistos = client.get(url, headers=luis).json()
    assert [(m["autor_nombre"], m["propio"]) for m in vistos] == [("Ana Pérez", False), ("Luis Gómez", True)]


def test_solo_conversan_los_involucrados(client, estudiante, admin):
    _, sid, _ = _solicitud(client, estudiante)
    url = f"/api/alianzas/{sid}/mensajes"
    client.post(url, json={"texto": "Hola"}, headers=estudiante)
    otro = registrar(client, "otro@ufpso.edu.co", nombre="Otra Persona")

    assert client.get(url, headers=otro).status_code == 403
    assert client.post(url, json={"texto": "Hola"}, headers=otro).status_code == 403
    assert len(client.get(url, headers=admin).json()) == 1
    assert client.get("/api/alianzas/00000000-0000-0000-0000-000000000000/mensajes", headers=estudiante).status_code == 404


def test_invitacion_tambien_tiene_conversacion(client, estudiante):
    pid = _proyecto(client, estudiante)
    maria = registrar(client, "maria@ufpso.edu.co", nombre="María Ruiz")
    inv = client.post(f"/api/proyectos/{pid}/invitaciones", json={"usuario_id": _yo(client, maria)["id"]}, headers=estudiante).json()
    res = client.post(f"/api/alianzas/{inv['id']}/mensajes", json={"texto": "¿Cuántas horas a la semana serían?"}, headers=maria)
    assert res.status_code == 201


def test_al_decidir_la_conversacion_queda_como_historial(client, estudiante):
    _, sid, luis = _solicitud(client, estudiante)
    url = f"/api/alianzas/{sid}/mensajes"
    m = client.post(url, json={"texto": "Antes de aceptar, ¿puedes los sábados?"}, headers=estudiante).json()
    client.post(f"/api/alianzas/{sid}/rechazar", json={}, headers=estudiante)

    assert client.post(url, json={"texto": "Sí puedo"}, headers=luis).status_code == 409
    assert client.patch(f"{url}/{m['id']}", json={"texto": "x"}, headers=estudiante).status_code == 409
    assert [x["texto"] for x in client.get(url, headers=luis).json()] == ["Antes de aceptar, ¿puedes los sábados?"]


def test_no_leidos_de_solicitudes_en_mis_chats(client, estudiante):
    pid, sid, luis = _solicitud(client, estudiante)
    url = f"/api/alianzas/{sid}/mensajes"
    # Sin mensajes, la solicitud no aparece como chat
    assert [c["tipo"] for c in client.get("/api/chats", headers=estudiante).json()] == ["proyecto"]

    ultimo = client.post(url, json={"texto": "¿Revisaste mi perfil?"}, headers=luis).json()
    [chat] = [c for c in client.get("/api/chats", headers=estudiante).json() if c["tipo"] == "solicitud"]
    assert chat["solicitud_id"] == sid and chat["proyecto_id"] == pid
    assert chat["titulo"].startswith("Luis Gómez · ") and chat["no_leidos"] == 1

    [del_otro_lado] = [c for c in client.get("/api/chats", headers=luis).json() if c["tipo"] == "solicitud"]
    assert del_otro_lado["titulo"].startswith("Ana Pérez · ") and del_otro_lado["no_leidos"] == 0

    client.post(f"{url}/leidos", json={"hasta_id": ultimo["id"]}, headers=estudiante)
    assert all(c["no_leidos"] == 0 for c in client.get("/api/chats", headers=estudiante).json())
