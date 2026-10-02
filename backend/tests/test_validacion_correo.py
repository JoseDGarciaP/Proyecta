import pytest

from app.core import validacion_correo
from app.core.validacion_correo import CorreoNoValido, sugerir_dominio, validar
from app.core.validacion_correo import dominio_recibe_correo as DNS_REAL  # antes de que las pruebas lo reemplacen


def registro(client, email, rol="aliado"):
    return client.post("/api/auth/registro", json={"email": email, "password": "clave-segura", "nombre": "Persona", "rol": rol})


@pytest.mark.parametrize("escrito, sugerido", [
    ("gmial.com", "gmail.com"),
    ("gmail.con", "gmail.com"),
    ("hotmial.com", "hotmail.com"),
    ("hotmail.co", "hotmail.com"),
    ("outlok.com", "outlook.com"),
    ("ufpso.edu.com", "ufpso.edu.co"),
    ("ufpso.eud.co", "ufpso.edu.co"),
])
def test_sugiere_dominio_por_error_de_tipeo(escrito, sugerido):
    assert sugerir_dominio(escrito) == sugerido


@pytest.mark.parametrize("dominio", ["yopmail.com", "gmail.com", "ufpso.edu.co", "ufps.edu.co", "mail.com", "empresa.co", "unal.edu.co"])
def test_no_corrige_dominios_reales(dominio):
    assert sugerir_dominio(dominio) is None


def test_normaliza_mayusculas_y_espacios():
    assert validar("  Ana.Perez@UFPSO.edu.co ").email == "ana.perez@ufpso.edu.co"


@pytest.mark.parametrize("email", ["ana", "ana@", "@ufpso.edu.co", "ana@@ufpso.edu.co", "ana perez@ufpso.edu.co", "ana@ufpso"])
def test_rechaza_formato(email):
    with pytest.raises(CorreoNoValido, match="formato"):
        validar(email)


@pytest.mark.parametrize("email", ["x@mailinator.com", "x@10minutemail.com", "x@yopmail.com", "x@sub.mailinator.com"])
def test_rechaza_desechables(email):
    with pytest.raises(CorreoNoValido, match="desechables"):
        validar(email)


def test_rechaza_dominio_sin_correo():
    with pytest.raises(CorreoNoValido, match="no recibe"):
        validar("x@dominio-inventado.com")


def test_registro_muestra_sugerencia(client):
    res = registro(client, "ana@gmial.com")
    assert res.status_code == 400
    assert "ana@gmail.com" in res.json()["detail"]


def test_registro_rechaza_dominio_inexistente(client):
    res = registro(client, "contacto@dominio-inventado.com")
    assert res.status_code == 400
    assert "no recibe" in res.json()["detail"]


def test_registro_rechaza_desechable(client):
    assert registro(client, "spam@yopmail.com").status_code == 400


def test_registro_guarda_correo_normalizado(client):
    res = registro(client, "  Ana@UFPSO.edu.co", rol="estudiante")
    assert res.status_code == 201
    assert res.json()["email"] == "ana@ufpso.edu.co"


def test_cuenta_sin_confirmar_no_aparta_el_correo(client):
    """Si alguien registró un correo ajeno, el dueño real puede registrarse y confirmar."""
    from tests.conftest import auth, token_del_correo

    assert client.post("/api/auth/registro", json={
        "email": "luis@ufpso.edu.co", "password": "clave-del-intruso", "nombre": "Intruso"}).status_code == 201
    res = client.post("/api/auth/registro", json={
        "email": "luis@ufpso.edu.co", "password": "clave-segura", "nombre": "Luis Real"})
    assert res.status_code == 201
    assert client.post("/api/auth/verificar", json={"token": token_del_correo("luis@ufpso.edu.co")}).status_code == 200
    yo = client.get("/api/usuarios/yo", headers=auth(client, "luis@ufpso.edu.co"))
    assert yo.json()["nombre"] == "Luis Real"
    assert client.post("/api/auth/login", data={"username": "luis@ufpso.edu.co", "password": "clave-del-intruso"}).status_code == 401


def test_ingreso_ignora_mayusculas_y_espacios(client, estudiante):
    res = client.post("/api/auth/login", data={"username": " ANA@ufpso.edu.co ", "password": "clave-segura"})
    assert res.status_code == 200


def test_dns_caido_no_bloquea(monkeypatch):
    monkeypatch.setattr(validacion_correo, "dominio_recibe_correo", lambda d: None)
    assert validar("x@empresa-nueva.co").dominio == "empresa-nueva.co"


def test_null_mx_y_nxdomain_reales():
    """Con red: example.com publica «MX 0 .» (no recibe correo). Se salta si no hay DNS."""
    real = DNS_REAL
    resultado = real("example.com")
    if resultado is None:
        pytest.skip("Sin acceso a DNS")
    assert resultado is False
    assert real("gmail.com") is True
