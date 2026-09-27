from tests.conftest import registrar

PROYECTO = {
    "titulo": "Riego inteligente para cebolla",
    "resumen": "Sensores de humedad y riego automático para pequeños productores.",
    "area": "Agroindustria",
    "estado": "ejecucion",
    "avance": 40,
    "presupuesto": 28_500_000,
    "equipo": ["Laura", "Andrés"],
    "etiquetas": ["IoT", "agua"],
    "ods": [2, 6],
}


def test_crear_y_leer(client, estudiante):
    res = client.post("/api/proyectos", json=PROYECTO, headers=estudiante)
    assert res.status_code == 201, res.text
    p = res.json()
    assert p["area"] == "Agroindustria"
    assert p["lider"] == "Ana Pérez"  # sin líder explícito se usa quien registra
    assert p["ods"] == [2, 6]
    assert p["actores"] == []
    assert client.get(f"/api/proyectos/{p['id']}").json()["titulo"] == PROYECTO["titulo"]


def test_crear_requiere_sesion(client):
    assert client.post("/api/proyectos", json=PROYECTO).status_code == 401


def test_validaciones(client, estudiante):
    assert client.post("/api/proyectos", json={**PROYECTO, "area": "Astrología"}, headers=estudiante).status_code == 422
    assert client.post("/api/proyectos", json={**PROYECTO, "ods": [99]}, headers=estudiante).status_code == 422
    assert client.post("/api/proyectos", json={**PROYECTO, "avance": 120}, headers=estudiante).status_code == 422
    assert client.post("/api/proyectos", json={**PROYECTO, "fecha_inicio": "2026-05-01",
                                                "fecha_fin": "2026-01-01"}, headers=estudiante).status_code == 422


def test_filtros(client, estudiante):
    client.post("/api/proyectos", json=PROYECTO, headers=estudiante)
    client.post("/api/proyectos", json={**PROYECTO, "titulo": "Tutorías entre pares", "area": "Educación",
                                        "estado": "idea", "ods": [4], "etiquetas": ["lectura"]}, headers=estudiante)
    assert len(client.get("/api/proyectos").json()) == 2
    assert len(client.get("/api/proyectos", params={"area": "Educación"}).json()) == 1
    assert len(client.get("/api/proyectos", params={"ods": 6}).json()) == 1
    assert len(client.get("/api/proyectos", params={"estado": "idea"}).json()) == 1
    assert len(client.get("/api/proyectos", params={"q": "lectura"}).json()) == 1


def test_solo_el_autor_edita(client, estudiante):
    pid = client.post("/api/proyectos", json=PROYECTO, headers=estudiante).json()["id"]
    otro = registrar(client, "otro@ufpso.edu.co", "Otro Usuario")
    assert client.patch(f"/api/proyectos/{pid}", json={"avance": 50}, headers=otro).status_code == 403
    res = client.patch(f"/api/proyectos/{pid}", json={"avance": 50, "area": "Tecnología"}, headers=estudiante)
    assert res.status_code == 200
    assert (res.json()["avance"], res.json()["area"]) == (50, "Tecnología")
    assert client.delete(f"/api/proyectos/{pid}", headers=otro).status_code == 403
    assert client.delete(f"/api/proyectos/{pid}", headers=estudiante).status_code == 204


def test_vincular_actores(client, estudiante, admin):
    actor = client.post("/api/actores", json={"nombre": "Alcaldía de Ocaña", "tipo": "estado"}, headers=admin).json()
    pid = client.post("/api/proyectos", json={**PROYECTO, "actores": [actor["id"]]}, headers=estudiante).json()["id"]
    assert client.get(f"/api/proyectos/{pid}").json()["actores"] == [actor["id"]]
    actores = client.get("/api/actores").json()
    assert actores[0]["proyectos"] == 1
