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
                                            "abre_en": str(date.today() - timedelta(days=30)),
                                            "cierra_en": str(date.today() - timedelta(days=1))}, headers=admin)
    assert len(client.get("/api/oportunidades", headers=admin).json()) == 2
    abiertas = client.get("/api/oportunidades", params={"abiertas": True}, headers=admin).json()
    assert [o["titulo"] for o in abiertas] == [OPORTUNIDAD["titulo"]]


def test_fecha_apertura_y_validacion_cierre(client, admin):
    """Ep6-Hu1: valida que la fecha de cierre sea estrictamente mayor a la fecha de apertura."""
    hoy = str(date.today())
    ayer = str(date.today() - timedelta(days=1))
    assert client.post("/api/oportunidades", json={**OPORTUNIDAD, "abre_en": hoy, "cierra_en": hoy}, headers=admin).status_code == 422
    assert client.post("/api/oportunidades", json={**OPORTUNIDAD, "abre_en": hoy, "cierra_en": ayer}, headers=admin).status_code == 422
    res = client.post("/api/oportunidades", json={**OPORTUNIDAD, "abre_en": ayer, "cierra_en": hoy}, headers=admin)
    assert res.status_code == 201
    assert res.json()["abre_en"] == ayer and res.json()["cierra_en"] == hoy


def test_dias_restantes_y_detalle(client, admin):
    """HU-04: cada convocatoria dice cuántos días faltan para el cierre y tiene su detalle."""
    creada = client.post("/api/oportunidades", json=OPORTUNIDAD, headers=admin).json()
    assert creada["dias_restantes"] == 30
    detalle = client.get(f"/api/oportunidades/{creada['id']}", headers=admin).json()
    assert detalle["dias_restantes"] == 30 and detalle["titulo"] == OPORTUNIDAD["titulo"]


def test_catalogo(client):
    assert len(client.get("/api/catalogo/ods").json()) == 17
    assert "Tecnología" in {a["nombre"] for a in client.get("/api/catalogo/areas").json()}
