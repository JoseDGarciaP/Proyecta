import pytest

from app.core import correo
from app.core.security import create_access_token, create_token
from app.modules.auth import google
from tests.conftest import auth, token_del_correo

DATOS = {"email": "ana@ufpso.edu.co", "password": "clave-segura", "nombre": "Ana Pérez"}


@pytest.mark.parametrize("ruta", ["/api/proyectos", "/api/oportunidades", "/api/actores", "/api/usuarios",
                                  "/api/perfil", "/api/alianzas", "/api/ia/buscar?q=agua", "/api/ia/estado"])
def test_visitantes_no_ven_datos(client, ruta):
    assert client.get(ruta).status_code == 401


def test_lo_publico(client, estudiante):
    cifras = client.get("/api/publico/cifras").json()
    assert cifras == {"proyectos": 0, "actores": 0, "oportunidades_abiertas": 0, "personas": 1}
    assert client.get("/api/catalogo/areas").status_code == 200
    assert client.get("/api/auth/config").json() == {"google_client_id": None, "dominios": ["ufpso.edu.co"]}


def test_registro_exige_confirmar_el_correo(client):
    res = client.post("/api/auth/registro", json=DATOS)
    assert res.status_code == 201 and res.json()["verificado"] is False

    mensaje = correo.enviados[-1]
    assert mensaje.para == "ana@ufpso.edu.co" and "http://localhost:5173/verificar?token=" in mensaje.texto

    login = client.post("/api/auth/login", data={"username": DATOS["email"], "password": DATOS["password"]})
    assert login.status_code == 403 and "Confirma tu correo" in login.json()["detail"]

    res = client.post("/api/auth/verificar", json={"token": token_del_correo(DATOS["email"])})
    assert res.status_code == 200
    yo = client.get("/api/usuarios/yo", headers={"Authorization": f"Bearer {res.json()['access_token']}"}).json()
    assert yo["verificado"] is True
    auth(client, DATOS["email"])  # ahora sí puede ingresar con contraseña


def test_tokens_no_se_intercambian(client):
    usuario_id = client.post("/api/auth/registro", json=DATOS).json()["id"]
    verificar = token_del_correo(DATOS["email"])
    # El enlace del correo no sirve como sesión…
    assert client.get("/api/usuarios/yo", headers={"Authorization": f"Bearer {verificar}"}).status_code == 401
    # …ni una sesión (o un token vencido, o basura) sirve para verificar.
    for token in (create_access_token(usuario_id), create_token(usuario_id, "verificar", -1), "basura"):
        assert client.post("/api/auth/verificar", json={"token": token}).status_code == 400


def test_sesion_de_cuenta_sin_verificar_no_entra(client):
    usuario_id = client.post("/api/auth/registro", json=DATOS).json()["id"]
    headers = {"Authorization": f"Bearer {create_access_token(usuario_id)}"}
    assert client.get("/api/proyectos", headers=headers).status_code == 403


def test_reenviar_no_revela_cuentas(client):
    assert client.post("/api/auth/reenviar-verificacion", json={"email": "nadie@ufpso.edu.co"}).status_code == 202
    assert correo.enviados == []
    client.post("/api/auth/registro", json=DATOS)
    assert client.post("/api/auth/reenviar-verificacion", json={"email": "ANA@ufpso.edu.co"}).status_code == 202
    assert len(correo.enviados) == 2


def _google(monkeypatch, **cuenta):
    datos = {"sub": "g-123", "email": "jose@ufpso.edu.co", "email_verified": True, "name": "José García", **cuenta}
    monkeypatch.setattr(google, "verificar", lambda credential: datos)


def test_ingreso_con_google_crea_cuenta_verificada(client, monkeypatch):
    _google(monkeypatch)
    res = client.post("/api/auth/google", json={"credential": "x"})
    assert res.status_code == 200
    yo = client.get("/api/usuarios/yo", headers={"Authorization": f"Bearer {res.json()['access_token']}"}).json()
    assert (yo["nombre"], yo["email"], yo["rol"], yo["verificado"]) == ("José García", "jose@ufpso.edu.co", "estudiante", True)
    # La segunda vez entra a la misma cuenta
    otra = client.post("/api/auth/google", json={"credential": "x"}).json()["access_token"]
    assert client.get("/api/usuarios/yo", headers={"Authorization": f"Bearer {otra}"}).json()["id"] == yo["id"]


def test_google_vincula_cuenta_existente_y_la_verifica(client, monkeypatch):
    creada = client.post("/api/auth/registro", json=DATOS).json()
    _google(monkeypatch, email="ana@ufpso.edu.co")
    token = client.post("/api/auth/google", json={"credential": "x"}).json()["access_token"]
    yo = client.get("/api/usuarios/yo", headers={"Authorization": f"Bearer {token}"}).json()
    assert yo["id"] == creada["id"] and yo["nombre"] == "Ana Pérez" and yo["verificado"] is True


def test_google_rechaza_otros_dominios_y_correos_sin_verificar(client, monkeypatch):
    _google(monkeypatch, email="jose@gmail.com")
    assert client.post("/api/auth/google", json={"credential": "x"}).status_code == 403
    _google(monkeypatch, email_verified=False)
    assert client.post("/api/auth/google", json={"credential": "x"}).status_code == 401


def test_google_sin_configurar(client):
    res = client.post("/api/auth/google", json={"credential": "x"})
    assert res.status_code == 401 and "no está configurado" in res.json()["detail"]


def test_verificacion_real_del_token_de_google(monkeypatch):
    """Firma un ID token como lo haría Google y comprueba firma, audiencia y emisor."""
    import time
    from types import SimpleNamespace

    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa

    from app.core.config import Settings

    privada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(google, "get_settings", lambda: Settings(google_client_id="cliente.apps.googleusercontent.com"))
    monkeypatch.setattr(google, "_llaves", lambda: SimpleNamespace(
        get_signing_key_from_jwt=lambda _: SimpleNamespace(key=privada.public_key())))

    def firmar(**cambios):
        datos = {"iss": "https://accounts.google.com", "aud": "cliente.apps.googleusercontent.com", "sub": "1",
                 "email": "ana@ufpso.edu.co", "email_verified": True, "exp": int(time.time()) + 600, **cambios}
        return jwt.encode(datos, privada, algorithm="RS256")

    assert google.verificar(firmar())["email"] == "ana@ufpso.edu.co"
    for malo in (firmar(aud="otra-app"), firmar(iss="https://evil.example"), firmar(exp=int(time.time()) - 10),
                 jwt.encode({"aud": "cliente.apps.googleusercontent.com"}, "secreto", algorithm="HS256")):
        with pytest.raises(google.TokenGoogleInvalido):
            google.verificar(malo)


def test_el_correo_escapa_el_nombre(client):
    client.post("/api/auth/registro", json={**DATOS, "nombre": '<a href="https://phish.example">Ana</a>'})
    assert "<a href=\"https://phish.example\">" not in correo.enviados[-1].html
