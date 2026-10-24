"""Experiencia (XP), niveles, postulaciones a oportunidades y evidencias."""

from app.core import correo
from tests.conftest import APRUEBA, RECO, registrar
from tests.test_alianzas import _proyecto, _yo
from tests.test_roles_insignias import _cambiar_permisos, _id

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _mia(client, h):
    return client.get("/api/experiencia/mia", headers=h).json()


def _acciones(mia):
    return [m["accion"] for m in mia["historial"]]


def _oportunidad(client, admin, cierra="2030-12-31"):
    res = client.post("/api/oportunidades", json={"titulo": "Convocatoria de innovación", "tipo": "convocatoria", "cierra_en": cierra},
                      headers=admin)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def test_xp_por_registrar_proyecto_e_insignia_y_ingreso_diario(client, estudiante):
    _yo(client, estudiante)
    _yo(client, estudiante)
    _proyecto(client, estudiante)
    mia = _mia(client, estudiante)
    assert _acciones(mia).count("ingreso_diario") == 1  # una vez al día
    assert {"proyecto_registrado", "insignia_obtenida"} <= set(_acciones(mia))
    assert mia["xp"] == 2 + 50 + 20
    assert mia["nivel"]["nombre"] == "Curioso" and mia["nivel"]["posicion"] == 2
    sig = mia["siguiente"]
    assert sig["nivel"]["nombre"] == "Aprendiz" and sig["xp_faltante"] == 150 - 72 and sig["insignias_faltantes"] == 0
    aviso = next(a for a in client.get("/api/notificaciones", headers=estudiante).json() if a["tipo"] == "nivel")
    assert "Curioso" in aviso["titulo"]


def test_tope_diario_de_mensajes(client, estudiante):
    pid = _proyecto(client, estudiante)
    for i in range(23):
        client.post(f"/api/proyectos/{pid}/mensajes", json={"texto": f"Mensaje {i}"}, headers=estudiante)
    assert _acciones(_mia(client, estudiante)).count("mensaje_equipo") == 20


def test_xp_por_avance_finalizar_y_colaborar(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)
    assert "colaboracion_aprobada" in _acciones(_mia(client, luis))
    assert "integrante_sumado" in _acciones(_mia(client, estudiante))

    client.patch(f"/api/proyectos/{pid}", json={"avance": 55}, headers=estudiante)  # PROYECTO arranca en 40 %
    client.patch(f"/api/proyectos/{pid}", json={"avance": 58}, headers=estudiante)
    client.patch(f"/api/proyectos/{pid}", json={"avance": 45}, headers=estudiante)
    client.patch(f"/api/proyectos/{pid}", json={"avance": 52}, headers=estudiante)
    assert _acciones(_mia(client, luis)).count("proyecto_avanza") == 1  # solo el 50 %, una vez
    client.patch(f"/api/proyectos/{pid}", json={"avance": 100, "estado": "finalizado"}, headers=estudiante)
    luis_mia = _mia(client, luis)
    assert _acciones(luis_mia).count("proyecto_avanza") == 6 and "proyecto_finalizado" in _acciones(luis_mia)


def test_admin_edita_puntos_niveles_y_ajusta(client, admin, estudiante):
    acciones = {a["clave"]: a for a in client.get("/api/admin/experiencia/acciones", headers=admin).json()}
    a = acciones["proyecto_registrado"]
    client.put("/api/admin/experiencia/acciones/proyecto_registrado",
               json={**{k: a[k] for k in ("nombre", "descripcion", "tope_diario", "activo")}, "puntos": 0}, headers=admin)
    _proyecto(client, estudiante)
    assert "proyecto_registrado" not in _acciones(_mia(client, estudiante))

    uid = _id(client, estudiante)
    personas = client.get("/api/admin/experiencia/personas?q=ana", headers=admin).json()
    assert [p["id"] for p in personas] == [uid] and personas[0]["nivel"]["nombre"] == "Novato"
    assert client.get("/api/admin/experiencia/personas?q=ana", headers=estudiante).status_code == 403
    assert client.post("/api/admin/experiencia/ajustes", json={"usuario_id": uid, "puntos": 0, "motivo": "nada"}, headers=admin).status_code == 422
    res = client.post("/api/admin/experiencia/ajustes", json={"usuario_id": uid, "puntos": 500, "motivo": "Asistió al congreso"}, headers=admin)
    assert res.status_code == 200 and res.json()["historial"][0]["otorgado_por"] == "Admin"
    mia = _mia(client, estudiante)
    assert mia["nivel"]["nombre"] == "Colaborador" or mia["nivel"]["nombre"] == "Aprendiz"  # pide insignias además de XP
    client.post("/api/admin/experiencia/ajustes", json={"usuario_id": uid, "puntos": -1000, "motivo": "Corrección de error"}, headers=admin)
    assert _mia(client, estudiante)["xp"] == 0 and _mia(client, estudiante)["nivel"]["nombre"] == "Novato"


def test_niveles_editables(client, admin, estudiante):
    niveles = client.get("/api/experiencia/niveles", headers=estudiante).json()
    assert [n["nombre"] for n in niveles][:3] == ["Novato", "Curioso", "Aprendiz"] and len(niveles) == 9
    insignias = {i["nombre"]: i["id"] for i in client.get("/api/admin/insignias", headers=admin).json()}
    curioso = niveles[1]
    res = client.put(f"/api/admin/experiencia/niveles/{curioso['id']}", json={
        "nombre": "Curioso", "icono": "eye", "color": "sky", "xp_minima": 10, "insignias_minimas": 0,
        "insignias_requeridas": [insignias["Perfil completo"]]}, headers=admin)
    assert res.status_code == 200, res.text
    _proyecto(client, estudiante)
    mia = _mia(client, estudiante)
    assert mia["nivel"]["nombre"] == "Novato" and mia["siguiente"]["requeridas_faltantes"] == ["Perfil completo"]
    client.patch("/api/usuarios/yo", json={"bio": "Hola", "habilidades": ["SIG"], "intereses": ["agua"]}, headers=estudiante)
    assert _mia(client, estudiante)["nivel"]["nombre"] in ("Curioso", "Aprendiz")
    assert client.post("/api/admin/experiencia/niveles", json={"nombre": "curioso"}, headers=admin).status_code == 409
    assert client.post("/api/admin/experiencia/niveles", json={"nombre": "Maestro", "icono": "dragon"}, headers=admin).status_code == 422
    assert client.get("/api/admin/experiencia/acciones", headers=estudiante).status_code == 403


def test_ranking_y_experiencia_de(client, admin, estudiante):
    _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    _yo(client, luis)
    for periodo in ("semana", "mes", "siempre"):
        r = client.get(f"/api/experiencia/ranking?periodo={periodo}", headers=luis).json()
        assert r[0]["nombre"] == "Ana Pérez" and r[0]["posicion"] == 1
    uid = _id(client, estudiante)
    de = client.get(f"/api/experiencia/de?ids={uid},x", headers=luis).json()
    assert de[uid]["xp"] > 0 and de[uid]["nivel"]["nombre"] == "Curioso"
    assert client.get(f"/api/usuarios/{uid}/perfil", headers=luis).json()["nivel"]["nombre"] == "Curioso"


def test_postulaciones(client, admin, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    oid = _oportunidad(client, admin)
    url = f"/api/oportunidades/{oid}/postulaciones"
    datos = {"proyecto_id": pid, "nota": "Nuestro piloto de riego encaja con la línea de agua."}
    assert client.post(url, json=datos, headers=luis).status_code == 403  # no es del equipo
    res = client.post(url, json=datos, headers=estudiante)
    assert res.status_code == 201, res.text
    post = res.json()
    assert client.post(url, json=datos, headers=estudiante).status_code == 409
    assert "postulacion_enviada" in _acciones(_mia(client, estudiante))
    assert any(a["tipo"] == "revision" for a in client.get("/api/notificaciones", headers=admin).json())
    cerrada = _oportunidad(client, admin, cierra="2020-01-01")
    assert client.post(f"/api/oportunidades/{cerrada}/postulaciones", json=datos, headers=estudiante).status_code == 409

    adm = f"/api/admin/postulaciones/{post['id']}"
    assert client.patch(adm, json={"estado": "no_seleccionada"}, headers=admin).status_code == 422
    res = client.patch(adm, json={"estado": "aceptada", "comentario": "¡Felicitaciones!"}, headers=admin)
    assert res.status_code == 200 and res.json()["estado"] == "aceptada"
    assert "postulacion_aceptada" in _acciones(_mia(client, estudiante))
    aviso = next(a for a in client.get("/api/notificaciones", headers=estudiante).json() if a["tipo"] == "postulacion")
    assert "seleccionado" in aviso["titulo"]
    assert [p["estado"] for p in client.get(f"/api/proyectos/{pid}/postulaciones", headers=luis).json()] == ["aceptada"]
    assert client.patch(adm, json={"estado": "aceptada"}, headers=estudiante).status_code == 403


def test_retirar_y_volver_a_postular(client, admin, estudiante):
    pid = _proyecto(client, estudiante)
    oid = _oportunidad(client, admin)
    datos = {"proyecto_id": pid, "nota": "Encaja muy bien con la convocatoria."}
    post = client.post(f"/api/oportunidades/{oid}/postulaciones", json=datos, headers=estudiante).json()
    assert client.post(f"/api/postulaciones/{post['id']}/retirar", headers=estudiante).json()["estado"] == "retirada"
    assert client.post(f"/api/oportunidades/{oid}/postulaciones", json=datos, headers=estudiante).status_code == 201
    assert _acciones(_mia(client, estudiante)).count("postulacion_enviada") == 1  # no da XP dos veces


def _subir(client, h, contenido=PDF, nombre="certificado.pdf", mime="application/pdf", **datos):
    return client.post("/api/evidencias", headers=h, data={"titulo": "Certificado de participación", **datos},
                       files={"archivo": (nombre, contenido, mime)})


def test_evidencias_subir_revisar_y_xp(client, admin, estudiante):
    pid = _proyecto(client, estudiante)
    assert _subir(client, estudiante, b"no soy pdf").status_code == 415
    assert _subir(client, estudiante, b"MZ\x90", "virus.exe", "application/octet-stream").status_code == 415
    res = _subir(client, estudiante, proyecto_id=pid, descripcion="Feria de ciencia 2026")
    assert res.status_code == 201, res.text
    ev = res.json()
    assert ev["estado"] == "pendiente" and ev["proyecto_titulo"] == "Riego inteligente para cebolla"
    assert _subir(client, estudiante, PNG, "foto.png", "image/png", tipo="foto").status_code == 201
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    assert client.get(f"/api/evidencias/{ev['id']}/archivo", headers=luis).status_code == 404  # pendiente y ajena
    assert client.get(f"/api/evidencias/{ev['id']}/archivo", headers=estudiante).content == PDF
    assert any(a["tipo"] == "revision" for a in client.get("/api/notificaciones", headers=admin).json())

    pendientes = client.get("/api/admin/evidencias?estado=pendiente", headers=admin).json()
    assert len(pendientes) == 2
    url = f"/api/admin/evidencias/{ev['id']}/revisar"
    assert client.post(url, json={"aprobar": False}, headers=admin).status_code == 422
    res = client.post(url, json={"aprobar": True, "puntos": 80, "comentario": "Excelente"}, headers=admin)
    assert res.status_code == 200 and res.json()["xp_otorgada"] == 80
    assert client.post(url, json={"aprobar": True}, headers=admin).status_code == 409
    mov = next(m for m in _mia(client, estudiante)["historial"] if m["accion"] == "evidencia")
    assert mov["puntos"] == 80 and mov["otorgado_por"] == "Admin"
    assert client.get(f"/api/evidencias/{ev['id']}/archivo", headers=luis).status_code == 200  # aprobada
    assert [e["titulo"] for e in client.get(f"/api/proyectos/{pid}/evidencias", headers=luis).json()] == ["Certificado de participación"]
    assert client.delete(f"/api/evidencias/{ev['id']}", headers=estudiante).status_code == 409
    otra = next(e for e in client.get("/api/evidencias/mias", headers=estudiante).json() if e["tipo"] == "foto")
    assert client.delete(f"/api/evidencias/{otra['id']}", headers=estudiante).status_code == 204


def test_permisos_de_postular_y_subir(client, admin, estudiante):
    _cambiar_permisos(client, admin, "estudiante", quitar=["evidencias.subir", "oportunidades.postular"])
    pid = _proyecto(client, estudiante)
    oid = _oportunidad(client, admin)
    assert _subir(client, estudiante).status_code == 403
    assert client.post(f"/api/oportunidades/{oid}/postulaciones", json={"proyecto_id": pid, "nota": "Una nota suficientemente larga"},
                       headers=estudiante).status_code == 403


def test_insignia_por_experiencia(client, admin, estudiante):
    res = client.post("/api/admin/insignias", json={"nombre": "Cien puntos", "icono": "zap", "color": "amber",
                                                    "reglas": {"condiciones": [{"criterio": "xp_total", "umbral": 100}]}}, headers=admin)
    assert res.status_code == 201
    uid = _id(client, estudiante)
    correo.enviados.clear()
    client.post("/api/admin/experiencia/ajustes", json={"usuario_id": uid, "puntos": 150, "motivo": "Mentoría a otro equipo"}, headers=admin)
    client.post("/api/admin/insignias/evaluar", headers=admin)
    nombres = {i["nombre"] for i in client.get("/api/insignias/mias", headers=estudiante).json()["obtenidas"]}
    assert "Cien puntos" in nombres
