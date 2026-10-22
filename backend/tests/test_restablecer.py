from app.core import correo
from tests.conftest import auth, token_del_correo


def pedir_enlace(client, email="ana@ufpso.edu.co"):
    res = client.post("/api/auth/recuperar", json={"email": email})
    assert res.status_code == 202
    return token_del_correo(email)


def test_restablecer_cambia_la_contrasena_e_inicia_sesion(client, estudiante):
    res = client.post("/api/auth/restablecer", json={"token": pedir_enlace(client), "password": "otra-clave-nueva"})
    assert res.status_code == 200
    nuevo = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get("/api/usuarios/yo", headers=nuevo).json()["email"] == "ana@ufpso.edu.co"
    # Entra con la nueva y ya no con la anterior.
    auth(client, "ana@ufpso.edu.co", "otra-clave-nueva")
    viejo = client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "clave-segura"})
    assert viejo.status_code == 401


def test_el_enlace_sirve_una_sola_vez(client, estudiante):
    token = pedir_enlace(client)
    assert client.post("/api/auth/restablecer", json={"token": token, "password": "primera-clave"}).status_code == 200
    res = client.post("/api/auth/restablecer", json={"token": token, "password": "segunda-clave"})
    assert res.status_code == 400


def test_correo_desconocido_no_revela_nada(client):
    res = client.post("/api/auth/recuperar", json={"email": "nadie@ufpso.edu.co"})
    assert res.status_code == 202
    assert correo.enviados == []


def test_enlace_invalido_o_de_otro_tipo(client, estudiante):
    assert client.post("/api/auth/restablecer", json={"token": "basura", "password": "clave-nueva-1"}).status_code == 400
    # Un token de sesión no sirve para cambiar la contraseña.
    sesion = estudiante["Authorization"].split()[1]
    assert client.post("/api/auth/restablecer", json={"token": sesion, "password": "clave-nueva-1"}).status_code == 400


def test_contrasena_nueva_corta(client, estudiante):
    res = client.post("/api/auth/restablecer", json={"token": pedir_enlace(client), "password": "corta"})
    assert res.status_code == 422


def test_restablecer_confirma_una_cuenta_sin_verificar(client):
    client.post("/api/auth/registro", json={"email": "luis@ufpso.edu.co", "password": "clave-segura", "nombre": "Luis Rojas"})
    token = pedir_enlace(client, "luis@ufpso.edu.co")
    assert client.post("/api/auth/restablecer", json={"token": token, "password": "clave-nueva-1"}).status_code == 200
    auth(client, "luis@ufpso.edu.co", "clave-nueva-1")
