def test_registro_y_perfil(client, estudiante):
    res = client.get("/api/usuarios/yo", headers=estudiante)
    assert res.status_code == 200
    assert res.json()["email"] == "ana@ufpso.edu.co"
    assert res.json()["rol"] == "estudiante"


def test_rechaza_correo_no_institucional(client):
    res = client.post("/api/auth/registro", json={"email": "ana@gmail.com", "password": "clave-segura", "nombre": "Ana Pérez"})
    assert res.status_code == 400


def test_aliado_puede_usar_otro_correo(client):
    res = client.post("/api/auth/registro", json={
        "email": "contacto@empresa.com", "password": "clave-segura", "nombre": "Empresa X", "rol": "aliado"})
    assert res.status_code == 201


def test_no_se_registra_admin(client):
    res = client.post("/api/auth/registro", json={
        "email": "yo@ufpso.edu.co", "password": "clave-segura", "nombre": "Yo mismo", "rol": "admin"})
    assert res.status_code == 400


def test_correo_duplicado(client, estudiante):
    res = client.post("/api/auth/registro", json={"email": "ANA@ufpso.edu.co", "password": "clave-segura", "nombre": "Otra Ana"})
    assert res.status_code == 409


def test_contrasena_incorrecta(client, estudiante):
    res = client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "incorrecta"})
    assert res.status_code == 401


def test_actualizar_perfil(client, estudiante):
    res = client.patch("/api/usuarios/yo", headers=estudiante, json={"habilidades": ["Python", "React"]})
    assert res.status_code == 200
    assert res.json()["habilidades"] == ["Python", "React"]


def test_token_requerido(client):
    assert client.get("/api/usuarios/yo").status_code == 401
    assert client.get("/api/usuarios/yo", headers={"Authorization": "Bearer basura"}).status_code == 401
