"""Formato fijo de solicitudes e invitaciones, motivos obligatorios y avisos (campana + correo)."""

from datetime import timedelta

from app.core import correo
from app.core.database import utcnow
from app.modules.notificaciones.servicio import enviar_resumenes
from tests.conftest import APRUEBA, RECHAZA, RECO, registrar
from tests.test_alianzas import _proyecto, _yo


def _avisos(client, headers):
    """Avisos sin los de insignias (esos los prueba test_roles_insignias.py)."""
    return [a for a in client.get("/api/notificaciones", headers=headers).json() if a["tipo"] not in ("insignia", "nivel")]


def _correos(para):
    return [c for c in correo.enviados if c.para == para]


def test_parametros_de_colaboracion(client, estudiante):
    p = client.get("/api/parametros/colaboracion", headers=estudiante).json()
    assert {m["tipo"] for m in p["motivos"]} == {"aprobacion", "rechazo"}
    assert any(m["requiere_comentario"] for m in p["motivos"])
    assert p["tipos_aporte"][0]["nombre"] == "Desarrollo de software"
    assert {x["para"] for x in p["plantillas"]} == {"solicitante", "responsable", "todos"}


def test_solicitud_exige_el_formato(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    url = f"/api/proyectos/{pid}/solicitudes"
    assert client.post(url, json={"mensaje": "hola"}, headers=luis).status_code == 422
    assert client.post(url, json={**RECO, "aporte": "corto"}, headers=luis).status_code == 422
    assert client.post(url, json={**RECO, "disponibilidad_horas": 0}, headers=luis).status_code == 422
    assert client.post(url, json={**RECO, "tipo_aporte_id": 999}, headers=luis).status_code == 422

    res = client.post(url, json={**RECO, "habilidades": [" Python ", "Python", ""]}, headers=luis)
    assert res.status_code == 201, res.text
    s = res.json()
    assert s["rol_propuesto"] == "Desarrollo de software"
    assert s["habilidades"] == ["Python"]
    assert s["disponibilidad_horas"] == 6


def test_aviso_y_correo_al_solicitar_y_al_decidir(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    correo.enviados.clear()
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]

    # El responsable recibe el aviso en la campana y el correo con la propuesta.
    avisos = _avisos(client, estudiante)
    assert avisos[0]["tipo"] == "solicitud_nueva" and avisos[0]["enlace"] == f"/perfil#solicitud-{sid}"
    assert sum(not a["leida"] for a in _avisos(client, estudiante)) == 1
    [mail] = _correos("ana@ufpso.edu.co")
    assert "Luis Gómez" in mail.asunto + mail.texto and "Desarrollo de software" in mail.texto and "6 horas" in mail.texto

    # Motivo obligatorio y del tipo correcto.
    url = f"/api/alianzas/{sid}"
    assert client.post(f"{url}/aceptar", json={}, headers=estudiante).status_code == 422
    assert client.post(f"{url}/aceptar", json=RECHAZA, headers=estudiante).status_code == 422  # motivo de rechazo
    assert client.post(f"{url}/rechazar", json={"motivo_id": 11}, headers=estudiante).status_code == 422  # «Otro» sin comentario
    res = client.post(f"{url}/rechazar", json={**RECHAZA, "respuesta": "Quizá el próximo semestre"}, headers=estudiante)
    assert res.status_code == 200, res.text
    assert res.json()["motivo_nombre"] == "El equipo ya está completo"

    aviso = _avisos(client, luis)[0]
    assert aviso["tipo"] == "solicitud_rechazada" and "equipo ya está completo" in aviso["cuerpo"]
    mail = _correos("luis@ufpso.edu.co")[-1]
    assert "rechazó" in mail.asunto and "Quizá el próximo semestre" in mail.texto


def test_aprobar_pone_el_rol_propuesto_al_miembro(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json={**RECO, "tipo_aporte_id": 2}, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)
    [m] = client.get(f"/api/proyectos/{pid}/miembros", headers=estudiante).json()
    assert m["rol"] == "Diseño y experiencia de usuario"
    assert _avisos(client, luis)[0]["enlace"] == f"/proyectos/{pid}"


def test_invitacion_avisa_al_invitado_y_la_cancelacion_tambien(client, estudiante):
    pid = _proyecto(client, estudiante)
    maria = registrar(client, "maria@ufpso.edu.co", nombre="María Ruiz")
    inv = client.post(f"/api/proyectos/{pid}/invitaciones", json={**RECO, "usuario_id": _yo(client, maria)["id"]},
                      headers=estudiante).json()
    assert _avisos(client, maria)[0]["tipo"] == "invitacion_nueva"
    client.post(f"/api/alianzas/{inv['id']}/cancelar", headers=estudiante)
    assert _avisos(client, maria)[0]["tipo"] == "solicitud_cancelada"


def test_preferencias_apagan_el_correo_pero_no_la_campana(client, estudiante):
    assert client.put("/api/notificaciones/preferencias", json={"solicitudes": False, "respuestas": True, "mensajes": True},
                      headers=estudiante).json()["solicitudes"] is False
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    correo.enviados.clear()
    client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis)
    assert _correos("ana@ufpso.edu.co") == []
    aviso = _avisos(client, estudiante)[0]
    assert aviso["correo_enviado"] is False


def test_marcar_leidas(client, estudiante):
    pid = _proyecto(client, estudiante)
    for i, email in enumerate(["a1@ufpso.edu.co", "a2@ufpso.edu.co"]):
        h = registrar(client, email, nombre=f"Persona {i}")
        client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=h)
    avisos = _avisos(client, estudiante)
    client.post(f"/api/notificaciones/{avisos[0]['id']}/leida", headers=estudiante)
    assert sum(not a["leida"] for a in _avisos(client, estudiante)) == 1
    client.post("/api/notificaciones/leidas", headers=estudiante)
    assert client.get("/api/notificaciones/conteo", headers=estudiante).json()["no_leidas"] == 0
    assert client.get("/api/notificaciones?solo_no_leidas=true", headers=estudiante).json() == []


def test_resumen_de_mensajes_sin_leer_se_envia_una_vez(client, db, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/mensajes", json={"texto": "¿Puedes los sábados?"}, headers=estudiante)
    client.post(f"/api/alianzas/{sid}/mensajes", json={"texto": "Es para el trabajo de campo"}, headers=estudiante)
    correo.enviados.clear()

    assert enviar_resumenes(db) == 0  # aún no pasan los 30 minutos de espera
    en_una_hora = utcnow() + timedelta(hours=1)
    assert enviar_resumenes(db, en_una_hora) == 1
    [mail] = _correos("luis@ufpso.edu.co")
    assert "2 mensajes sin leer" in mail.asunto
    assert enviar_resumenes(db, en_una_hora + timedelta(minutes=10)) == 0  # no se repite el aviso por los mismos mensajes
    assert _avisos(client, luis)[0]["tipo"] == "mensajes_sin_leer"
