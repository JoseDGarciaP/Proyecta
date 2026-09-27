from datetime import date, timedelta

from tests.test_proyectos import PROYECTO


def _oportunidad(admin, client, **cambios):
    datos = {"titulo": "Fondo agroindustrial", "entidad": "Cámara de Comercio", "tipo": "financiacion",
             "cierra_en": str(date.today() + timedelta(days=20)), "areas": ["Agroindustria"], "ods": [2], **cambios}
    return client.post("/api/oportunidades", json=datos, headers=admin).json()


def test_recomienda_con_explicacion(client, estudiante, admin):
    afin = _oportunidad(admin, client)
    _oportunidad(admin, client, titulo="Fondo de salud", areas=["Salud"], ods=[3])
    _oportunidad(admin, client, titulo="Fondo agro vencido", cierra_en=str(date.today() - timedelta(days=1)))
    pid = client.post("/api/proyectos", json=PROYECTO, headers=estudiante).json()["id"]

    res = client.post(f"/api/ia/proyectos/{pid}/analisis")
    assert res.status_code == 200
    cuerpo = res.json()
    assert cuerpo["simulado"] is True  # sin API key
    assert "Riego inteligente" in cuerpo["resumen"]
    assert [r["oportunidad_id"] for r in cuerpo["recomendaciones"]] == [afin["id"]]
    razon = cuerpo["recomendaciones"][0]["razon"]
    assert "Agroindustria" in razon and "ODS 2" in razon


def test_proyecto_inexistente(client):
    assert client.post("/api/ia/proyectos/00000000-0000-0000-0000-000000000000/analisis").status_code == 404
