from datetime import date, timedelta

OPORTUNIDAD = {
    "titulo": "Convocatoria de semilleros 2027",
    "entidad": "Minciencias",
    "tipo": "convocatoria",
    "monto": 50_000_000,
    "cierra_en": str(date.today() + timedelta(days=30)),
    "areas": ["Tecnología"],
    "ods": [9],
}


def test_solo_admin_crea(client, estudiante, admin):
    assert client.post("/api/oportunidades", json=OPORTUNIDAD, headers=estudiante).status_code == 403
    assert client.post("/api/actores", json={"nombre": "Empresa X", "tipo": "empresa"}, headers=estudiante).status_code == 403
    res = client.post("/api/oportunidades", json=OPORTUNIDAD, headers=admin)
    assert res.status_code == 201
    assert res.json()["areas"] == ["Tecnología"]


def test_filtro_abiertas(client, admin):
    client.post("/api/oportunidades", json=OPORTUNIDAD, headers=admin)
    client.post("/api/oportunidades", json={**OPORTUNIDAD, "titulo": "Convocatoria vencida",
                                            "cierra_en": str(date.today() - timedelta(days=1))}, headers=admin)
    assert len(client.get("/api/oportunidades").json()) == 2
    abiertas = client.get("/api/oportunidades", params={"abiertas": True}).json()
    assert [o["titulo"] for o in abiertas] == [OPORTUNIDAD["titulo"]]


def test_catalogo(client):
    assert len(client.get("/api/catalogo/ods").json()) == 17
    assert "Tecnología" in {a["nombre"] for a in client.get("/api/catalogo/areas").json()}
