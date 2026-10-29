from app.core import correo
from tests.conftest import APRUEBA, RECO, auth, registrar
from tests.test_proyectos import PROYECTO


def _proyecto(client, headers):
    res = client.post("/api/proyectos", json=PROYECTO, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _invitar(client, headers, pid, email):
    return client.post(f"/api/proyectos/{pid}/invitaciones-correo", json={**RECO, "email": email}, headers=headers)


def _token_invitacion(email):
    mensaje = next(c for c in reversed(correo.enviados) if c.para == email and "invitacion?token=" in c.texto)
    return mensaje.texto.split("invitacion?token=")[1].split()[0]


def _miembros(client, headers, pid):
    return [m["nombre"] for m in client.get(f"/api/proyectos/{pid}/miembros", headers=headers).json()]


def _registro(client, email, nombre, **extra):
    return client.post("/api/auth/registro", json={"email": email, "password": "Clave-Segura1", "nombre": nombre, **extra})


def test_acepta_desde_el_correo_y_al_registrarse_queda_en_el_equipo(client, estudiante):
    pid = _proyecto(client, estudiante)
    res = _invitar(client, estudiante, pid, "Nuevo@UFPSO.edu.co")
    assert res.status_code == 201, res.text
    assert res.json()["modo"] == "correo" and res.json()["invitacion"]["email"] == "nuevo@ufpso.edu.co"
    token = _token_invitacion("nuevo@ufpso.edu.co")

    # Repetida mientras sigue pendiente
    assert _invitar(client, estudiante, pid, "nuevo@ufpso.edu.co").status_code == 409
    # El responsable la ve en su lista
    lista = client.get(f"/api/proyectos/{pid}/invitaciones-correo", headers=estudiante).json()
    assert [i["email"] for i in lista] == ["nuevo@ufpso.edu.co"]

    # Sin sesión, desde el enlace
    vista = client.get(f"/api/invitaciones/{token}").json()
    assert vista["proyecto_id"] == pid and vista["cuenta_existe"] is False and vista["estado"] == "pendiente"
    assert vista["invitado_por"] == "Ana Pérez"
    assert client.post(f"/api/invitaciones/{token}/aceptar").json()["estado"] == "aceptada"
    assert client.post(f"/api/invitaciones/{token}/rechazar").status_code == 409

    # Al registrarse con el código del enlace la cuenta queda confirmada y entra al equipo
    res = _registro(client, "nuevo@ufpso.edu.co", "Nora Nueva", invitacion=token)
    assert res.status_code == 201, res.text
    assert res.json()["verificado"] is True
    nora = auth(client, "nuevo@ufpso.edu.co")
    assert _miembros(client, estudiante, pid) == ["Nora Nueva"]
    perfil = client.get("/api/perfil", headers=nora).json()
    assert perfil["proyectos"][0]["mi_rol"] == "colaborador"
    assert perfil["alianzas"][0]["estado"] == "aceptada"
    assert client.get(f"/api/proyectos/{pid}/invitaciones-correo", headers=estudiante).json() == []
    assert client.get(f"/api/invitaciones/{token}").json()["es_miembro"] is True
    # Al responsable le llega el aviso
    avisos = client.get("/api/notificaciones", headers=estudiante).json()
    assert any("Nora Nueva aceptó" in a["titulo"] for a in (avisos["items"] if isinstance(avisos, dict) else avisos))


def test_si_se_registra_sin_aceptar_la_invitacion_queda_pendiente_en_su_perfil(client, estudiante):
    pid = _proyecto(client, estudiante)
    _invitar(client, estudiante, pid, "luis@ufpso.edu.co")
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")  # registro normal con verificación
    pendientes = [s for s in client.get("/api/alianzas", headers=luis).json() if s["por_responder"]]
    assert len(pendientes) == 1 and pendientes[0]["tipo"] == "invitacion" and pendientes[0]["proyecto_id"] == pid
    assert _miembros(client, estudiante, pid) == []
    client.post(f"/api/alianzas/{pendientes[0]['id']}/aceptar", json=APRUEBA, headers=luis)
    assert _miembros(client, estudiante, pid) == ["Luis Gómez"]


def test_codigo_de_otro_correo_no_confirma_la_cuenta(client, estudiante):
    pid = _proyecto(client, estudiante)
    _invitar(client, estudiante, pid, "invitada@ufpso.edu.co")
    token = _token_invitacion("invitada@ufpso.edu.co")
    res = _registro(client, "otra@ufpso.edu.co", "Otra Persona", invitacion=token)
    assert res.status_code == 201 and res.json()["verificado"] is False
    # La invitación sigue esperando a su dueña
    assert len(client.get(f"/api/proyectos/{pid}/invitaciones-correo", headers=estudiante).json()) == 1


def test_correo_con_cuenta_recibe_invitacion_normal(client, estudiante):
    pid = _proyecto(client, estudiante)
    maria = registrar(client, "maria@ufpso.edu.co", nombre="María Ruiz")
    res = _invitar(client, estudiante, pid, "maria@ufpso.edu.co")
    assert res.status_code == 201 and res.json()["modo"] == "usuario"
    assert res.json()["solicitud"]["usuario_nombre"] == "María Ruiz"
    assert [s["por_responder"] for s in client.get("/api/alianzas", headers=maria).json()] == [True]


def test_rechazar_y_cancelar(client, estudiante):
    pid = _proyecto(client, estudiante)
    _invitar(client, estudiante, pid, "a@ufpso.edu.co")
    token = _token_invitacion("a@ufpso.edu.co")
    assert client.post(f"/api/invitaciones/{token}/rechazar").json()["estado"] == "rechazada"
    assert client.post(f"/api/invitaciones/{token}/aceptar").status_code == 409
    registrar(client, "a@ufpso.edu.co", nombre="Andrés")  # al registrarse no aparece nada
    assert client.get("/api/alianzas", headers=auth(client, "a@ufpso.edu.co")).json() == []

    inv = _invitar(client, estudiante, pid, "b@ufpso.edu.co").json()["invitacion"]
    token_b = _token_invitacion("b@ufpso.edu.co")
    otro = registrar(client, "otro@ufpso.edu.co", nombre="Otro Usuario")
    assert client.post(f"/api/invitaciones-correo/{inv['id']}/cancelar", headers=otro).status_code == 403
    assert client.post(f"/api/invitaciones-correo/{inv['id']}/cancelar", headers=estudiante).json()["estado"] == "cancelada"
    assert client.post(f"/api/invitaciones/{token_b}/aceptar").status_code == 409


def test_solo_el_responsable_invita_y_token_invalido(client, estudiante):
    pid = _proyecto(client, estudiante)
    otro = registrar(client, "otro@ufpso.edu.co", nombre="Otro Usuario")
    assert _invitar(client, otro, pid, "x@ufpso.edu.co").status_code == 403
    assert client.get(f"/api/proyectos/{pid}/invitaciones-correo", headers=otro).status_code == 403
    assert client.get("/api/invitaciones/no-existe").status_code == 404
    assert _invitar(client, estudiante, pid, "x@dominio-inventado.com").status_code == 400


def test_vencida(client, estudiante, db):
    from datetime import timedelta

    from app.core.database import utcnow
    from app.modules.alianzas.models import InvitacionCorreo

    pid = _proyecto(client, estudiante)
    _invitar(client, estudiante, pid, "tarde@ufpso.edu.co")
    token = _token_invitacion("tarde@ufpso.edu.co")
    inv = db.query(InvitacionCorreo).one()
    inv.expira_en = utcnow() - timedelta(days=1)
    db.commit()
    assert client.get(f"/api/invitaciones/{token}").json()["vencida"] is True
    assert client.post(f"/api/invitaciones/{token}/aceptar").status_code == 410
    # Se puede volver a invitar al mismo correo
    assert _invitar(client, estudiante, pid, "tarde@ufpso.edu.co").status_code == 201


def test_ya_registrado_sin_confirmar_acepta_y_al_confirmar_entra(client, estudiante):
    pid = _proyecto(client, estudiante)
    assert _registro(client, "lenta@ufpso.edu.co", "Lenta").status_code == 201  # sin confirmar aún
    assert _invitar(client, estudiante, pid, "lenta@ufpso.edu.co").json()["modo"] == "correo"
    token = _token_invitacion("lenta@ufpso.edu.co")
    assert client.post(f"/api/invitaciones/{token}/aceptar").status_code == 200
    verificacion = next(c for c in correo.enviados if c.para == "lenta@ufpso.edu.co" and "verificar?token=" in c.texto)
    token_verificar = verificacion.texto.split("verificar?token=")[1].split()[0]
    assert client.post("/api/auth/verificar", json={"token": token_verificar}).status_code == 200
    assert _miembros(client, estudiante, pid) == ["Lenta"]
