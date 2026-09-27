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
    assert cuerpo["simulado"] is True  # sin modelo configurado
    assert "Riego inteligente" in cuerpo["resumen"]
    assert [r["oportunidad_id"] for r in cuerpo["recomendaciones"]] == [afin["id"]]
    razon = cuerpo["recomendaciones"][0]["razon"]
    assert "Agroindustria" in razon and "ODS 2" in razon


def test_proyecto_inexistente(client):
    assert client.post("/api/ia/proyectos/00000000-0000-0000-0000-000000000000/analisis").status_code == 404


def _usar_proveedor(monkeypatch, proveedor, manejador):
    import httpx

    from app.core.config import Settings
    from app.modules.ia import servicio

    monkeypatch.setattr(servicio, "get_settings", lambda: Settings(ia_proveedor=proveedor, anthropic_api_key="x"))
    monkeypatch.setattr(servicio, "_transporte", httpx.MockTransport(manejador))


def test_resumen_con_ollama(client, estudiante, monkeypatch):
    import httpx

    pedidos = []

    def ollama(request):
        pedidos.append(request)
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "  Resumen del modelo.  "}})

    _usar_proveedor(monkeypatch, "ollama", ollama)
    pid = client.post("/api/proyectos", json=PROYECTO, headers=estudiante).json()["id"]
    cuerpo = client.post(f"/api/ia/proyectos/{pid}/analisis").json()
    assert (cuerpo["resumen"], cuerpo["simulado"]) == ("Resumen del modelo.", False)
    assert pedidos[0].url.path == "/api/chat"


def test_ollama_caido_usa_reglas(client, estudiante, monkeypatch):
    import httpx

    def caido(request):
        raise httpx.ConnectError("sin conexión", request=request)

    _usar_proveedor(monkeypatch, "ollama", caido)
    pid = client.post("/api/proyectos", json=PROYECTO, headers=estudiante).json()["id"]
    cuerpo = client.post(f"/api/ia/proyectos/{pid}/analisis").json()
    assert cuerpo["simulado"] is True
    assert "Riego inteligente" in cuerpo["resumen"]


def test_resumen_con_anthropic(client, estudiante, monkeypatch):
    import httpx

    _usar_proveedor(monkeypatch, "anthropic",
                    lambda r: httpx.Response(200, json={"content": [{"type": "text", "text": "Resumen de Claude."}]}))
    pid = client.post("/api/proyectos", json=PROYECTO, headers=estudiante).json()["id"]
    cuerpo = client.post(f"/api/ia/proyectos/{pid}/analisis").json()
    assert (cuerpo["resumen"], cuerpo["simulado"]) == ("Resumen de Claude.", False)
