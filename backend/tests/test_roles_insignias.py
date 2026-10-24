"""Roles con permisos editables, roles personalizados e insignias (automáticas y manuales)."""

from app.core import correo
from tests.conftest import APRUEBA, RECO, registrar
from tests.test_alianzas import _proyecto, _yo
from tests.test_proyectos import PROYECTO


def _rol(client, admin, clave):
    return next(r for r in client.get("/api/admin/roles", headers=admin).json() if r["clave"] == clave)


def _cambiar_permisos(client, admin, clave, quitar=(), agregar=()):
    r = _rol(client, admin, clave)
    permisos = (set(r["permisos"]) - set(quitar)) | set(agregar)
    res = client.put(f"/api/admin/roles/{clave}", json={**{k: r[k] for k in ("nombre", "descripcion", "institucional", "registro_publico")},
                                                       "permisos": sorted(permisos)}, headers=admin)
    assert res.status_code == 200, res.text
    return res.json()


def _id(client, headers):
    return _yo(client, headers)["id"]


# ---- Roles y permisos ------------------------------------------------------------------------

def test_permisos_por_defecto(client, estudiante, admin):
    yo = _yo(client, estudiante)
    assert yo["rol_nombre"] == "Estudiante"
    assert "proyectos.crear" in yo["permisos"] and not any(p.startswith("admin.") for p in yo["permisos"])
    assert "admin.roles" in _yo(client, admin)["permisos"]
    assert client.get("/api/admin/roles", headers=estudiante).status_code == 403


def test_quitar_permisos_a_un_rol(client, estudiante, admin):
    _cambiar_permisos(client, admin, "estudiante", quitar=["proyectos.crear", "oportunidades.ver"])
    res = client.post("/api/proyectos", json=PROYECTO, headers=estudiante)
    assert res.status_code == 403 and "registrar proyectos" in res.json()["detail"]
    assert client.get("/api/oportunidades", headers=estudiante).status_code == 403
    assert "proyectos.crear" not in _yo(client, estudiante)["permisos"]
    registro = client.get("/api/admin/registro", headers=admin).json()[0]
    assert registro["accion"] == "rol.editar" and "Registrar proyectos" in registro["detalle"]


def test_el_rol_administrador_conserva_todo(client, admin):
    r = _cambiar_permisos(client, admin, "admin", quitar=["admin.usuarios"])
    assert "admin.usuarios" in r["permisos"]
    assert client.get("/api/admin/usuarios", headers=admin).status_code == 200
    assert client.delete("/api/admin/roles/admin", headers=admin).status_code == 409


def test_rol_personalizado_con_parte_del_panel(client, admin, estudiante):
    res = client.post("/api/admin/roles", json={"nombre": "Coordinador de semillero", "descripcion": "Modera proyectos",
                                               "permisos": ["proyectos.crear", "admin.moderacion", "oportunidades.gestionar"]},
                      headers=admin)
    assert res.status_code == 201, res.text
    assert res.json()["clave"] == "coordinador_de_semillero"
    assert client.post("/api/admin/roles", json={"nombre": "Otro", "permisos": ["admin.roles"]}, headers=admin).status_code == 422
    assert client.post("/api/admin/roles", json={"nombre": "coordinador de semillero"}, headers=admin).status_code == 409

    uid = _id(client, estudiante)
    assert client.patch(f"/api/admin/usuarios/{uid}", json={"rol": "coordinador_de_semillero"}, headers=admin).status_code == 200
    yo = _yo(client, estudiante)
    assert yo["rol_nombre"] == "Coordinador de semillero"
    assert client.get("/api/admin/proyectos", headers=estudiante).status_code == 200
    assert client.get("/api/admin/usuarios", headers=estudiante).status_code == 403
    assert client.get("/api/oportunidades", headers=estudiante).status_code == 403  # no tiene «ver oportunidades»
    assert client.post("/api/oportunidades", json={"titulo": "Convocatoria X", "tipo": "convocatoria", "cierra_en": "2030-01-01"},
                       headers=estudiante).status_code == 201


def test_quien_gestiona_usuarios_no_puede_hacerse_admin(client, admin, estudiante):
    client.post("/api/admin/roles", json={"nombre": "Soporte", "permisos": ["admin.usuarios"]}, headers=admin)
    yo = _id(client, estudiante)
    client.patch(f"/api/admin/usuarios/{yo}", json={"rol": "soporte"}, headers=admin)
    otro = registrar(client, "otro@ufpso.edu.co", nombre="Otra Persona")
    otro_id = _id(client, otro)
    assert client.patch(f"/api/admin/usuarios/{otro_id}", json={"rol": "admin"}, headers=estudiante).status_code == 403
    assert client.patch(f"/api/admin/usuarios/{yo}", json={"rol": "docente"}, headers=estudiante).status_code == 409
    admin_id = _id(client, admin)
    assert client.patch(f"/api/admin/usuarios/{admin_id}", json={"activo": False}, headers=estudiante).status_code == 403
    assert client.patch(f"/api/admin/usuarios/{otro_id}", json={"rol": "docente"}, headers=estudiante).status_code == 200


def test_eliminar_rol_con_personas_exige_reasignar(client, admin, estudiante):
    client.post("/api/admin/roles", json={"nombre": "Temporal"}, headers=admin)
    uid = _id(client, estudiante)
    client.patch(f"/api/admin/usuarios/{uid}", json={"rol": "temporal"}, headers=admin)
    assert client.delete("/api/admin/roles/temporal", headers=admin).status_code == 409
    assert client.delete("/api/admin/roles/temporal?reasignar_a=docente", headers=admin).status_code == 204
    assert _yo(client, estudiante)["rol"] == "docente"
    assert client.delete("/api/admin/roles/estudiante", headers=admin).status_code == 409  # del sistema


def test_roles_en_el_registro(client, admin):
    client.post("/api/admin/roles", json={"nombre": "Egresado", "registro_publico": True}, headers=admin)
    client.post("/api/admin/roles", json={"nombre": "Invitado", "registro_publico": True, "institucional": False}, headers=admin)
    client.post("/api/admin/roles", json={"nombre": "Interno"}, headers=admin)
    claves = [r["clave"] for r in client.get("/api/auth/roles").json()]
    assert "egresado" in claves and "interno" not in claves and "admin" not in claves
    base = {"password": "clave-segura", "nombre": "Persona Nueva"}
    assert client.post("/api/auth/registro", json={**base, "email": "e@ufpso.edu.co", "rol": "egresado"}).status_code == 201
    assert client.post("/api/auth/registro", json={**base, "email": "e2@gmail.com", "rol": "egresado"}).status_code == 400
    assert client.post("/api/auth/registro", json={**base, "email": "i@gmail.com", "rol": "invitado"}).status_code == 201
    assert client.post("/api/auth/registro", json={**base, "email": "x@ufpso.edu.co", "rol": "interno"}).status_code == 400
    assert client.post("/api/auth/registro", json={**base, "email": "y@ufpso.edu.co", "rol": "admin"}).status_code == 400


# ---- Insignias -------------------------------------------------------------------------------

def _mias(client, h):
    return client.get("/api/insignias/mias", headers=h).json()


def _nombres(lista):
    return {i["nombre"] for i in lista}


def test_insignia_automatica_al_registrar_proyecto(client, estudiante):
    correo.enviados.clear()
    _proyecto(client, estudiante)
    mias = _mias(client, estudiante)
    assert "Primer proyecto" in _nombres(mias["obtenidas"])
    emprendedor = next(e for e in mias["en_progreso"] if e["insignia"]["nombre"] == "Emprendedor/a")
    [cond] = emprendedor["condiciones"]
    assert (cond["actual"], cond["umbral"]) == (1, 3)
    assert "Mención de honor" in _nombres(mias["manuales_disponibles"])
    aviso = client.get("/api/notificaciones", headers=estudiante).json()[0]
    assert aviso["tipo"] == "insignia" and "Primer proyecto" in aviso["titulo"] and aviso["enlace"] == "/perfil#logros"
    assert any("Primer proyecto" in c.asunto for c in correo.enviados if c.para == "ana@ufpso.edu.co")


def test_insignias_al_aprobar_y_al_completar_perfil(client, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)
    assert "Colaborador/a" in _nombres(_mias(client, luis)["obtenidas"])
    client.patch("/api/usuarios/yo", json={"bio": "Me gusta programar", "habilidades": ["Python"], "intereses": ["agua"]}, headers=luis)
    assert "Perfil completo" in _nombres(_mias(client, luis)["obtenidas"])
    # Finalizar el proyecto da «Proyecto cumplido» a todo el equipo.
    client.patch(f"/api/proyectos/{pid}", json={"estado": "finalizado", "avance": 100}, headers=estudiante)
    assert "Proyecto cumplido" in _nombres(_mias(client, luis)["obtenidas"])
    assert "Proyecto cumplido" in _nombres(_mias(client, estudiante)["obtenidas"])


def test_preferencia_apaga_el_correo_de_logros(client, estudiante):
    client.put("/api/notificaciones/preferencias", json={"solicitudes": True, "respuestas": True, "mensajes": True, "logros": False},
               headers=estudiante)
    correo.enviados.clear()
    _proyecto(client, estudiante)
    assert not [c for c in correo.enviados if c.para == "ana@ufpso.edu.co"]
    assert client.get("/api/notificaciones", headers=estudiante).json()[0]["tipo"] == "insignia"


def test_otorgar_y_retirar_insignia_manual(client, admin, estudiante):
    insignias = {i["nombre"]: i for i in client.get("/api/admin/insignias", headers=admin).json()}
    mencion = insignias["Mención de honor"]["id"]
    uid = _id(client, estudiante)
    assert client.post(f"/api/admin/insignias/{mencion}/otorgar", json={"usuario_id": uid, "motivo": "no"}, headers=admin).status_code == 422
    res = client.post(f"/api/admin/insignias/{mencion}/otorgar", json={"usuario_id": uid, "motivo": "Ganó la feria de proyectos 2026"},
                      headers=admin)
    assert res.status_code == 200, res.text
    assert client.post(f"/api/admin/insignias/{mencion}/otorgar", json={"usuario_id": uid, "motivo": "Otra vez lo mismo"},
                       headers=admin).status_code == 409
    obtenida = next(i for i in _mias(client, estudiante)["obtenidas"] if i["nombre"] == "Mención de honor")
    assert obtenida["motivo"] == "Ganó la feria de proyectos 2026" and not obtenida["automatica"]
    [fila] = client.get(f"/api/admin/insignias/{mencion}/otorgadas", headers=admin).json()
    assert fila["otorgada_por"] == "Admin"
    assert client.get(f"/api/insignias/de?ids={uid},basura", headers=estudiante).json()[uid][0]["nombre"] == "Mención de honor"

    client.delete(f"/api/admin/insignias/{mencion}/otorgadas/{uid}", headers=admin)
    assert "Mención de honor" not in _nombres(_mias(client, estudiante)["obtenidas"])
    assert client.post(f"/api/admin/insignias/{mencion}/otorgar", json={"usuario_id": uid, "motivo": "Se la devolvemos"},
                       headers=admin).status_code == 200


def test_retirada_automatica_no_vuelve_sola(client, admin, estudiante):
    _proyecto(client, estudiante)
    primer = next(i for i in client.get("/api/admin/insignias", headers=admin).json() if i["nombre"] == "Primer proyecto")
    uid = _id(client, estudiante)
    client.delete(f"/api/admin/insignias/{primer['id']}/otorgadas/{uid}", headers=admin)
    client.post("/api/admin/insignias/evaluar", headers=admin)
    _proyecto(client, estudiante)
    assert "Primer proyecto" not in _nombres(_mias(client, estudiante)["obtenidas"])


def test_nueva_insignia_automatica_se_entrega_a_quien_ya_cumple(client, admin, estudiante):
    _proyecto(client, estudiante)
    assert client.post("/api/admin/insignias", json={"nombre": "Pionero", "icono": "nope"}, headers=admin).status_code == 422
    res = client.post("/api/admin/insignias", json={"nombre": "Pionero", "descripcion": "Un proyecto", "icono": "star", "color": "sky",
                                                   "reglas": {"condiciones": [{"criterio": "proyectos_registrados", "umbral": 1}]}}, headers=admin)
    assert res.status_code == 201 and res.json()["otorgadas"] == 1
    assert "Pionero" in _nombres(_mias(client, estudiante)["obtenidas"])


def test_ranking_y_perfil_publico(client, admin, estudiante):
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    ranking = client.get("/api/insignias/ranking", headers=luis).json()
    assert ranking[0]["nombre"] == "Ana Pérez" and ranking[0]["posicion"] == 1 and ranking[0]["total"] >= 1
    perfil = client.get(f"/api/usuarios/{_id(client, estudiante)}/perfil", headers=luis).json()
    assert perfil["usuario"]["rol_nombre"] == "Estudiante"
    assert perfil["proyectos"][0]["proyecto"]["id"] == pid and perfil["proyectos"][0]["rol"] == "Responsable"
    assert "Primer proyecto" in _nombres(perfil["insignias"])
    _cambiar_permisos(client, admin, "estudiante", quitar=["usuarios.ver"])
    assert client.get(f"/api/usuarios/{_id(client, estudiante)}/perfil", headers=luis).status_code == 403
    assert client.get("/api/insignias/ranking", headers=luis).status_code == 403


def test_buscar_candidatos_para_otorgar(client, admin, estudiante):
    res = client.get("/api/admin/insignias/candidatos?q=ana", headers=admin).json()
    assert [c["email"] for c in res] == ["ana@ufpso.edu.co"]
    assert client.get("/api/admin/insignias/candidatos?q=ana", headers=estudiante).status_code == 403



# ---- Reglas con varios requisitos, tipos, vigencia y entregas en grupo ------------------------

def _crear(client, admin, **datos):
    res = client.post("/api/admin/insignias", json={"icono": "star", "color": "teal", **datos}, headers=admin)
    assert res.status_code == 201, res.text
    return res.json()


def test_regla_con_varios_requisitos(client, admin, estudiante):
    ins = _crear(client, admin, nombre="Agroemprendedor", descripcion="Proyectos de agro con equipo",
                 reglas={"modo": "todas", "condiciones": [
                     {"criterio": "proyectos_en_area", "umbral": 1, "valor": "Agroindustria"},
                     {"criterio": "integrantes_sumados", "umbral": 1}]})
    assert ins["texto_regla"] == "Proyectos en un área «Agroindustria»: 1 o más y Personas sumadas a sus proyectos: 1 o más"
    pid = _proyecto(client, estudiante)  # PROYECTO es de Agroindustria
    mias = _mias(client, estudiante)
    assert "Agroemprendedor" not in _nombres(mias["obtenidas"])
    progreso = next(e for e in mias["en_progreso"] if e["insignia"]["nombre"] == "Agroemprendedor")
    assert [c["actual"] for c in progreso["condiciones"]] == [1, 0] and progreso["avance"] == 0.5
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)
    assert "Agroemprendedor" in _nombres(_mias(client, estudiante)["obtenidas"])


def test_regla_con_alguna_condicion_y_rol(client, admin, estudiante):
    _crear(client, admin, nombre="Cuerpo docente", tipo="reconocimiento",
           reglas={"modo": "alguna", "condiciones": [{"criterio": "es_rol", "valor": "docente"},
                                                     {"criterio": "programa", "valor": "licenciatura"}]})
    assert "Cuerpo docente" not in _nombres(_mias(client, estudiante)["obtenidas"])
    client.patch(f"/api/admin/usuarios/{_id(client, estudiante)}", json={"rol": "docente"}, headers=admin)
    assert "Cuerpo docente" in _nombres(_mias(client, estudiante)["obtenidas"])


def test_validaciones_de_reglas(client, admin):
    base = {"nombre": "Prueba", "icono": "star", "color": "teal"}
    malas = [
        {"condiciones": [{"criterio": "inventado"}]},
        {"condiciones": [{"criterio": "proyectos_en_area"}]},
        {"condiciones": [{"criterio": "proyectos_en_area", "valor": "Astrología"}]},
        {"condiciones": [{"criterio": "proyectos_con_ods", "valor": "40"}]},
        {"condiciones": [{"criterio": "es_rol", "valor": "rey"}]},
        {"condiciones": []},
    ]
    for reglas in malas:
        assert client.post("/api/admin/insignias", json={**base, "reglas": reglas}, headers=admin).status_code == 422, reglas
    assert client.post("/api/admin/insignias", json={**base, "icono": "dragon"}, headers=admin).status_code == 422
    opciones = client.get("/api/insignias/opciones", headers=admin).json()
    assert len(opciones["iconos"]) >= 60 and "teal" in opciones["colores"] and opciones["tipos"]["condecoracion"] == "Condecoración"


def test_condecoracion_con_entidad_y_fecha_y_vigencia(client, admin, estudiante):
    ins = _crear(client, admin, nombre="Destacado 2026-2", tipo="condecoracion", entidad="Facultad de Ingenierías",
                 vence_en="2026-12-15")
    uid = _id(client, estudiante)
    correo.enviados.clear()
    res = client.post(f"/api/admin/insignias/{ins['id']}/otorgar",
                      json={"usuario_id": uid, "motivo": "Mejor promedio del semestre", "fecha_evento": "2026-10-20"}, headers=admin)
    assert res.status_code == 200, res.text
    b = res.json()
    assert b["tipo"] == "condecoracion" and b["entidad"] == "Facultad de Ingenierías" and b["fecha_evento"] == "2026-10-20"
    assert b["vence_en"].startswith("2026-12-15")
    mail = [c for c in correo.enviados if c.para == "ana@ufpso.edu.co"][-1]
    assert "Condecoración" in mail.asunto and "Facultad de Ingenierías" in mail.texto


def test_insignia_vencida_sale_de_las_vigentes(client, admin, estudiante):
    ins = _crear(client, admin, nombre="Semestre pasado", tipo="reconocimiento")
    uid = _id(client, estudiante)
    client.post(f"/api/admin/insignias/{ins['id']}/otorgar",
                json={"usuario_id": uid, "motivo": "Del semestre anterior", "vence_en": "2020-01-01"}, headers=admin)
    mias = _mias(client, estudiante)
    assert "Semestre pasado" not in _nombres(mias["obtenidas"]) and "Semestre pasado" in _nombres(mias["vencidas"])
    [fila] = client.get(f"/api/admin/insignias/{ins['id']}/otorgadas", headers=admin).json()
    assert fila["estado"] == "vencida"
    # Se puede volver a otorgar.
    assert client.post(f"/api/admin/insignias/{ins['id']}/otorgar", json={"usuario_id": uid, "motivo": "De nuevo este semestre"},
                       headers=admin).status_code == 200


def test_vigencia_en_dias_para_automaticas(client, admin, estudiante):
    _crear(client, admin, nombre="Activo este mes", vigencia_dias=30, reglas={"condiciones": [{"criterio": "proyectos_registrados"}]})
    _proyecto(client, estudiante)
    b = next(i for i in _mias(client, estudiante)["obtenidas"] if i["nombre"] == "Activo este mes")
    assert b["vence_en"] is not None


def test_otorgar_a_varios_y_a_un_equipo(client, admin, estudiante):
    ins = _crear(client, admin, nombre="Equipo ganador", tipo="condecoracion")
    pid = _proyecto(client, estudiante)
    luis = registrar(client, "luis@ufpso.edu.co", nombre="Luis Gómez")
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=luis).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)
    maria = registrar(client, "maria@ufpso.edu.co", nombre="María Ruiz")
    url = f"/api/admin/insignias/{ins['id']}/otorgar-varios"
    assert client.post(url, json={"motivo": "Sin nadie"}, headers=admin).status_code == 422
    res = client.post(url, json={"proyecto_id": pid, "usuario_ids": [_id(client, maria)], "motivo": "Ganaron la feria 2026"},
                      headers=admin).json()
    assert sorted(res["otorgadas"]) == ["Ana Pérez", "Luis Gómez", "María Ruiz"] and res["ya_tenian"] == []
    res = client.post(url, json={"usuario_ids": [_id(client, luis)], "motivo": "Otra vez"}, headers=admin).json()
    assert res == {"otorgadas": [], "ya_tenian": ["Luis Gómez"]}
    proyectos = client.get("/api/admin/insignias/proyectos?q=riego", headers=admin).json()
    assert proyectos[0]["equipo"] == 2
