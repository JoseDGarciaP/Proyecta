from app.core import correo
from tests.conftest import APRUEBA, RECHAZA, RECO, auth, registrar, token_del_correo
from tests.test_alianzas import _proyecto, _yo


def test_solo_admin(client, estudiante):
    assert client.get("/api/admin/usuarios", headers=estudiante).status_code == 403
    assert client.get("/api/admin/estadisticas", headers=estudiante).status_code == 403


def test_listar_filtrar_y_editar_usuarios(client, admin, estudiante):
    pagina = client.get("/api/admin/usuarios?q=ana", headers=admin).json()
    assert pagina["total"] == 1
    ana = pagina["items"][0]
    assert ana["email"] == "ana@ufpso.edu.co" and ana["activo"] and ana["verificado"]

    res = client.patch(f"/api/admin/usuarios/{ana['id']}", json={"rol": "docente"}, headers=admin)
    assert res.json()["rol"] == "docente"
    aviso = client.get("/api/notificaciones", headers=estudiante).json()[0]
    assert aviso["tipo"] == "cuenta" and "Docente" in aviso["cuerpo"]

    client.patch(f"/api/admin/usuarios/{ana['id']}", json={"activo": False}, headers=admin)
    assert client.get("/api/usuarios/yo", headers=estudiante).status_code == 401
    assert client.get("/api/admin/usuarios?estado=inactivo", headers=admin).json()["total"] == 1
    registro = client.get("/api/admin/registro", headers=admin).json()
    assert registro[0]["accion"] == "usuario.editar" and "desactivada" in registro[0]["detalle"]


def test_no_quedarse_sin_admin(client, admin):
    yo = _yo(client, admin)
    assert client.patch(f"/api/admin/usuarios/{yo['id']}", json={"rol": "docente"}, headers=admin).status_code == 409
    assert client.patch(f"/api/admin/usuarios/{yo['id']}", json={"activo": False}, headers=admin).status_code == 409


def test_crear_usuario_envia_enlace_para_la_contrasena(client, admin):
    res = client.post("/api/admin/usuarios", json={"email": "Nuevo@ufpso.edu.co", "nombre": "Nuevo Docente", "rol": "docente"},
                      headers=admin)
    assert res.status_code == 201, res.text
    assert client.post("/api/admin/usuarios", json={"email": "nuevo@ufpso.edu.co", "nombre": "Otro"}, headers=admin).status_code == 409
    mail = [c for c in correo.enviados if c.para == "nuevo@ufpso.edu.co"][-1]
    assert "cuenta" in mail.asunto.lower()
    r = client.post("/api/auth/restablecer", json={"token": token_del_correo("nuevo@ufpso.edu.co"), "password": "Mi-Clave-Nueva1"})
    assert r.status_code == 200
    auth(client, "nuevo@ufpso.edu.co", "Mi-Clave-Nueva1")


def test_catalogo_de_motivos_y_tipos_de_aporte(client, admin, estudiante):
    m = client.post("/api/admin/motivos", json={"tipo": "rechazo", "nombre": "Convocatoria cerrada"}, headers=admin).json()
    nombres = [x["nombre"] for x in client.get("/api/parametros/colaboracion", headers=estudiante).json()["motivos"]]
    assert "Convocatoria cerrada" in nombres
    client.put(f"/api/admin/motivos/{m['id']}", json={"tipo": "rechazo", "nombre": "Convocatoria cerrada", "activo": False},
               headers=admin)
    nombres = [x["nombre"] for x in client.get("/api/parametros/colaboracion", headers=estudiante).json()["motivos"]]
    assert "Convocatoria cerrada" not in nombres
    assert client.post("/api/admin/tipos-aporte", json={"nombre": "desarrollo de software"}, headers=admin).status_code == 409

    # Un motivo inactivo ya no sirve para decidir.
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    assert client.post(f"/api/alianzas/{sid}/rechazar", json={"motivo_id": m["id"]}, headers=estudiante).status_code == 422


def test_areas_no_se_borran_si_estan_en_uso(client, admin, estudiante):
    _proyecto(client, estudiante)
    areas = {a["nombre"]: a for a in client.get("/api/admin/areas", headers=admin).json()}
    usada = next(a for a in areas.values() if a["proyectos"])
    assert client.delete(f"/api/admin/areas/{usada['id']}", headers=admin).status_code == 409
    nueva = client.post("/api/admin/areas", json={"nombre": "Turismo"}, headers=admin).json()
    assert client.post("/api/admin/areas", json={"nombre": "turismo"}, headers=admin).status_code == 409
    assert "Turismo" in [a["nombre"] for a in client.get("/api/catalogo/areas").json()]
    assert client.delete(f"/api/admin/areas/{nueva['id']}", headers=admin).status_code == 204
    assert client.put("/api/admin/ods/4", json={"nombre": "Educación de calidad para todos"}, headers=admin).status_code == 200


def test_ajustes_cambian_los_dominios_y_los_correos(client, admin):
    ajustes = client.get("/api/admin/ajustes", headers=admin).json()
    assert ajustes["dominios_permitidos"] == ["ufpso.edu.co"]
    assert client.put("/api/admin/ajustes", json={**ajustes, "dominios_permitidos": ["mal dominio"]}, headers=admin).status_code == 422
    client.put("/api/admin/ajustes", json={**ajustes, "dominios_permitidos": ["@ufpso.edu.co", "ejemplo.edu.co"],
                                           "correo_solicitudes": False}, headers=admin)
    assert client.get("/api/auth/config").json()["dominios"] == ["ufpso.edu.co", "ejemplo.edu.co"]
    registrar(client, "eva@ejemplo.edu.co", nombre="Eva Díaz")  # ahora se acepta ese dominio


def test_moderacion_quita_proyecto_y_avisa(client, admin, estudiante):
    pid = _proyecto(client, estudiante)
    [p] = client.get("/api/admin/proyectos", headers=admin).json()
    assert p["responsable_email"] == "ana@ufpso.edu.co"
    assert client.request("DELETE", f"/api/admin/proyectos/{pid}", json={"motivo": "no"}, headers=admin).status_code == 422
    res = client.request("DELETE", f"/api/admin/proyectos/{pid}", json={"motivo": "Contenido duplicado"}, headers=admin)
    assert res.status_code == 204
    aviso = client.get("/api/notificaciones", headers=estudiante).json()[0]
    assert aviso["tipo"] == "moderacion" and "duplicado" in aviso["cuerpo"]


def test_estadisticas(client, admin, estudiante):
    pid = _proyecto(client, estudiante)
    for i, (email, decision) in enumerate([("l1@ufpso.edu.co", APRUEBA), ("l2@ufpso.edu.co", RECHAZA)]):
        h = registrar(client, email, nombre=f"Persona {i}")
        sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=h).json()["id"]
        client.post(f"/api/alianzas/{sid}/{'aceptar' if decision is APRUEBA else 'rechazar'}", json=decision, headers=estudiante)
    e = client.get("/api/admin/estadisticas", headers=admin).json()
    assert e["tasa_aprobacion"] == 0.5
    assert {m["motivo"] for m in e["motivos"]} == {"Perfil adecuado para el proyecto", "El equipo ya está completo"}
    assert e["aportes"] == [{"clave": "Desarrollo de software", "total": 2}]
    assert e["correos_30_dias"] >= 4


def test_crear_usuario_exige_correo_institucional_salvo_aliados(client, admin):
    url = "/api/admin/usuarios"
    for rol in ("estudiante", "docente", "administrativo", "admin"):
        res = client.post(url, json={"email": f"{rol}@gmail.com", "nombre": "Persona Externa", "rol": rol}, headers=admin)
        assert res.status_code == 400, rol
        assert "@ufpso.edu.co" in res.json()["detail"]
    assert client.post(url, json={"email": "doc@ufpso.edu.co", "nombre": "Docente", "rol": "docente"}, headers=admin).status_code == 201
    res = client.post(url, json={"email": "empresa@gmail.com", "nombre": "Aliada Externa", "rol": "aliado"}, headers=admin)
    assert res.status_code == 201, res.text
    # Igual que el registro: errores de tipeo y correos desechables no pasan.
    assert client.post(url, json={"email": "otra@gmial.com", "nombre": "Aliada", "rol": "aliado"}, headers=admin).status_code == 400


def test_aliado_con_correo_personal_no_puede_pasar_a_rol_institucional(client, admin):
    res = client.post("/api/admin/usuarios", json={"email": "empresa@gmail.com", "nombre": "Aliada Externa", "rol": "aliado"}, headers=admin)
    uid = res.json()["id"]
    assert client.patch(f"/api/admin/usuarios/{uid}", json={"rol": "docente"}, headers=admin).status_code == 409
    assert client.patch(f"/api/admin/usuarios/{uid}", json={"nombre": "Aliada Renombrada"}, headers=admin).status_code == 200


def test_registro_publico_exige_correo_institucional_salvo_aliados(client):
    base = {"password": "Clave-Segura1", "nombre": "Persona Externa"}
    for rol in ("estudiante", "docente", "administrativo"):
        res = client.post("/api/auth/registro", json={**base, "email": f"{rol}@gmail.com", "rol": rol})
        assert res.status_code == 400 and "@ufpso.edu.co" in res.json()["detail"]
    assert client.post("/api/auth/registro", json={**base, "email": "empresa@gmail.com", "rol": "aliado"}).status_code == 201
