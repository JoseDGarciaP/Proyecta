from tests.conftest import APRUEBA, RECO, registrar
from tests.test_alianzas import _proyecto


def _con_colaborador(client, responsable):
    """Proyecto de `responsable` con Luis aceptado como colaborador."""
    pid = _proyecto(client, responsable)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=responsable)
    return pid, luis


def _enviar(client, pid, headers, texto):
    res = client.post(f"/api/proyectos/{pid}/mensajes", json={"texto": texto}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


def test_responsable_y_miembro_conversan(client, estudiante):
    pid, luis = _con_colaborador(client, estudiante)

    hola = _enviar(client, pid, estudiante, "  Hola equipo  ")
    assert hola["texto"] == "Hola equipo" and hola["autor_nombre"] == "Ana Pérez" and hola["propio"] is True
    _enviar(client, pid, luis, "¡Hola Ana!")

    vistos_por_luis = client.get(f"/api/proyectos/{pid}/mensajes", headers=luis).json()
    assert [(m["texto"], m["propio"]) for m in vistos_por_luis] == [("Hola equipo", False), ("¡Hola Ana!", True)]


def test_el_chat_es_privado(client, estudiante, admin):
    pid, _ = _con_colaborador(client, estudiante)
    _enviar(client, pid, estudiante, "Solo para el equipo")
    intruso = registrar(client, "intruso@ufpso.edu.co", nombre="Intruso")

    assert client.get(f"/api/proyectos/{pid}/mensajes", headers=intruso).status_code == 403
    assert client.post(f"/api/proyectos/{pid}/mensajes", json={"texto": "hola"}, headers=intruso).status_code == 403
    assert client.get(f"/api/proyectos/{pid}/mensajes").status_code == 401
    assert len(client.get(f"/api/proyectos/{pid}/mensajes", headers=admin).json()) == 1  # moderación


def test_quien_se_retira_pierde_el_acceso(client, estudiante):
    pid, luis = _con_colaborador(client, estudiante)
    luis_id = client.get("/api/usuarios/yo", headers=luis).json()["id"]
    client.delete(f"/api/proyectos/{pid}/miembros/{luis_id}", headers=luis)
    assert client.get(f"/api/proyectos/{pid}/mensajes", headers=luis).status_code == 403


def test_cursores_para_consultar_lo_nuevo_y_el_historial(client, estudiante):
    pid = _proyecto(client, estudiante)
    ids = [_enviar(client, pid, estudiante, f"m{i}")["id"] for i in range(5)]
    url = f"/api/proyectos/{pid}/mensajes"

    assert [m["texto"] for m in client.get(url, params={"limite": 2}, headers=estudiante).json()] == ["m3", "m4"]
    assert [m["texto"] for m in client.get(url, params={"despues_de": ids[2]}, headers=estudiante).json()] == ["m3", "m4"]
    assert client.get(url, params={"despues_de": ids[-1]}, headers=estudiante).json() == []
    anteriores = client.get(url, params={"antes_de": ids[3], "limite": 2}, headers=estudiante).json()
    assert [m["texto"] for m in anteriores] == ["m1", "m2"]


def test_mensajes_vacios_o_muy_largos(client, estudiante):
    pid = _proyecto(client, estudiante)
    assert client.post(f"/api/proyectos/{pid}/mensajes", json={"texto": "   "}, headers=estudiante).status_code == 422
    assert client.post(f"/api/proyectos/{pid}/mensajes", json={"texto": "x" * 2001}, headers=estudiante).status_code == 422


def test_editar_y_eliminar_solo_el_autor(client, estudiante, admin):
    pid, luis = _con_colaborador(client, estudiante)
    m = _enviar(client, pid, luis, "Mensaje con eror")
    url = f"/api/proyectos/{pid}/mensajes/{m['id']}"

    assert client.patch(url, json={"texto": "Otro"}, headers=estudiante).status_code == 403
    editado = client.patch(url, json={"texto": "Mensaje con error"}, headers=luis).json()
    assert editado["texto"] == "Mensaje con error" and editado["editado_en"] is not None

    assert client.delete(url, headers=estudiante).status_code == 403
    assert client.delete(url, headers=admin).status_code == 204
    [eliminado] = client.get(f"/api/proyectos/{pid}/mensajes", headers=luis).json()
    assert eliminado["eliminado"] is True and eliminado["texto"] == ""
    assert client.patch(url, json={"texto": "revivir"}, headers=luis).status_code == 404


def test_no_leidos_en_mis_chats(client, estudiante):
    pid, luis = _con_colaborador(client, estudiante)
    _proyecto(client, estudiante)  # un segundo proyecto, sin mensajes
    _enviar(client, pid, luis, "uno")
    ultimo = _enviar(client, pid, luis, "dos")

    chats = client.get("/api/chats", headers=estudiante).json()
    assert len(chats) == 2
    assert chats[0]["proyecto_id"] == pid and chats[0]["no_leidos"] == 2 and chats[0]["ultimo"]["texto"] == "dos"
    assert chats[1]["no_leidos"] == 0 and chats[1]["ultimo"] is None
    # Lo que escribe uno mismo no cuenta como no leído
    assert client.get("/api/chats", headers=luis).json()[0]["no_leidos"] == 0

    leer = client.post(f"/api/proyectos/{pid}/mensajes/leidos", json={"hasta_id": ultimo["id"]}, headers=estudiante)
    assert leer.status_code == 204
    assert client.get("/api/chats", headers=estudiante).json()[0]["no_leidos"] == 0
    # Marcar un id anterior no hace retroceder la lectura
    client.post(f"/api/proyectos/{pid}/mensajes/leidos", json={"hasta_id": 0}, headers=estudiante)
    assert client.get("/api/chats", headers=estudiante).json()[0]["no_leidos"] == 0


def test_la_consulta_periodica_trae_ediciones_y_eliminaciones(client, estudiante):
    pid, luis = _con_colaborador(client, estudiante)
    url = f"/api/proyectos/{pid}/mensajes"
    primero = _enviar(client, pid, luis, "Se va a borrar")
    segundo = _enviar(client, pid, luis, "Se va a editar")

    # Lo que Ana ya tiene en pantalla: el último id y la última modificación.
    vistos = client.get(url, headers=estudiante).json()
    cursor = {"despues_de": vistos[-1]["id"], "cambios_desde": max(m["modificado_en"] for m in vistos)}

    client.delete(f"{url}/{primero['id']}", headers=luis)
    client.patch(f"{url}/{segundo['id']}", json={"texto": "Editado"}, headers=luis)
    nuevo = _enviar(client, pid, luis, "Nuevo")

    cambios = {m["id"]: m for m in client.get(url, params=cursor, headers=estudiante).json()}
    assert cambios[primero["id"]]["eliminado"] is True
    assert cambios[segundo["id"]]["texto"] == "Editado"
    assert nuevo["id"] in cambios
    # Sin `cambios_desde` sigue trayendo solo lo nuevo
    assert [m["id"] for m in client.get(url, params={"despues_de": cursor["despues_de"]}, headers=estudiante).json()] == [nuevo["id"]]
