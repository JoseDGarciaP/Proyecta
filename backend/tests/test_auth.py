def test_registro_y_perfil(client, estudiante):
    res = client.get("/api/usuarios/yo", headers=estudiante)
    assert res.status_code == 200
    assert res.json()["email"] == "ana@ufpso.edu.co"
    assert res.json()["rol"] == "estudiante"


def test_rechaza_correo_no_institucional(client):
    res = client.post("/api/auth/registro", json={"email": "ana@gmail.com", "password": "Clave-Segura1", "acepta_datos": True, "nombre": "Ana Pérez"})
    assert res.status_code == 400


def test_aliado_puede_usar_otro_correo(client):
    res = client.post("/api/auth/registro", json={
        "email": "contacto@empresa.com", "password": "Clave-Segura1", "acepta_datos": True, "nombre": "Empresa X", "rol": "aliado"})
    assert res.status_code == 201


def test_no_se_registra_admin(client):
    res = client.post("/api/auth/registro", json={
        "email": "yo@ufpso.edu.co", "password": "Clave-Segura1", "acepta_datos": True, "nombre": "Yo mismo", "rol": "admin"})
    assert res.status_code == 400


def test_correo_duplicado(client, estudiante):
    res = client.post("/api/auth/registro", json={"email": "ANA@ufpso.edu.co", "password": "Clave-Segura1", "acepta_datos": True, "nombre": "Otra Ana"})
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


def test_registro_exige_contrasena_segura(client):
    datos = {"email": "eva@ufpso.edu.co", "nombre": "Eva Torres"}
    res = client.post("/api/auth/registro", json={**datos, "password": "clave-segura"})
    assert res.status_code == 422
    assert "una mayúscula" in res.json()["detail"][0]["msg"] and "un número" in res.json()["detail"][0]["msg"]
    assert client.post("/api/auth/registro", json={**datos, "password": "Clave-Segura1", "acepta_datos": True}).status_code == 201


def test_las_cuentas_anteriores_entran_con_su_contrasena(client, db):
    from app.core.security import hash_password
    from app.models import Usuario
    db.add(Usuario(email="viejo@ufpso.edu.co", nombre="Usuario Viejo", hashed_password=hash_password("clave-antigua"),
                   rol="estudiante", habilidades=[], intereses=[], verificado=True))
    db.commit()
    res = client.post("/api/auth/login", data={"username": "viejo@ufpso.edu.co", "password": "clave-antigua"})
    assert res.status_code == 200


# ---- Bloque 1: acceso y datos institucionales --------------------------------------------------

def test_registro_exige_aceptar_datos(client):
    res = client.post("/api/auth/registro", json={"email": "eva@ufpso.edu.co", "password": "Clave-Segura1", "nombre": "Eva Torres"})
    assert res.status_code == 400
    assert "tratamiento de datos" in res.json()["detail"]


def test_codigo_y_cedula_unicos(client):
    base = {"password": "Clave-Segura1", "acepta_datos": True, "nombre": "Persona Uno", "codigo": "1920001", "cedula": "1090000001", "sexo": "F"}
    assert client.post("/api/auth/registro", json={**base, "email": "uno@ufpso.edu.co"}).status_code == 201
    res = client.post("/api/auth/registro", json={**base, "email": "dos@ufpso.edu.co", "cedula": "1090000002"})
    assert res.status_code == 409 and "código" in res.json()["detail"]
    res = client.post("/api/auth/registro", json={**base, "email": "dos@ufpso.edu.co", "codigo": "1920002"})
    assert res.status_code == 409 and "cédula" in res.json()["detail"]


def test_datos_sensibles_no_son_publicos(client, estudiante, admin):
    from tests.conftest import registrar
    otro = registrar(client, "luis@ufpso.edu.co", "Luis Rojas", codigo="1920099", cedula="1090000099", sexo="M")
    yo = client.get("/api/usuarios/yo", headers=otro).json()
    assert yo["codigo"] == "1920099" and yo["cedula"] == "1090000099"
    publico = client.get(f"/api/usuarios/{yo['id']}", headers=estudiante).json()
    assert "codigo" not in publico and "cedula" not in publico and "sexo" not in publico
    # Desde el perfil no se pueden cambiar
    client.patch("/api/usuarios/yo", headers=otro, json={"codigo": "x", "cedula": "y"})
    assert client.get("/api/usuarios/yo", headers=otro).json()["codigo"] == "1920099"


def test_bloqueo_tras_cinco_intentos(client, estudiante):
    for _ in range(5):
        assert client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Mala-Clave1"}).status_code == 401
    # Bloqueada: ni siquiera con la contraseña correcta
    res = client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Clave-Segura1"})
    assert res.status_code == 429 and "bloqueada" in res.json()["detail"]


def test_bloqueo_vence(client, db, estudiante):
    from datetime import datetime, timedelta, timezone
    from app.models import Usuario
    for _ in range(5):
        client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Mala-Clave1"})
    usuario = db.query(Usuario).filter_by(email="ana@ufpso.edu.co").one()
    usuario.bloqueado_hasta = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    assert client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Clave-Segura1"}).status_code == 200


def test_intentos_se_reinician_al_entrar(client, estudiante):
    for _ in range(4):
        client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Mala-Clave1"})
    assert client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Clave-Segura1"}).status_code == 200
    for _ in range(4):
        client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Mala-Clave1"})
    assert client.post("/api/auth/login", data={"username": "ana@ufpso.edu.co", "password": "Clave-Segura1"}).status_code == 200


def test_cerrar_sesion_invalida_el_token(client, estudiante):
    assert client.get("/api/usuarios/yo", headers=estudiante).status_code == 200
    assert client.post("/api/auth/salir", headers=estudiante).status_code == 204
    assert client.get("/api/usuarios/yo", headers=estudiante).status_code == 401


def test_buscar_personas_por_habilidad(client, estudiante, admin):
    client.patch("/api/usuarios/yo", headers=estudiante, json={"habilidades": ["Python"], "intereses": ["Tecnología"]})
    nombres = [u["nombre"] for u in client.get("/api/usuarios?q=python", headers=admin).json()]
    assert "Ana Pérez" in nombres
    nombres = [u["nombre"] for u in client.get("/api/usuarios?q=Tecnolog", headers=admin).json()]
    assert "Ana Pérez" in nombres
