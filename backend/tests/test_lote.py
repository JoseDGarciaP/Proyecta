"""Carga de proyectos por lote desde el Excel del formulario de registro."""

import io
from datetime import datetime

from openpyxl import Workbook

from app.core import correo
from app.models import Usuario
from app.modules.notificaciones.models import Notificacion
from app.modules.proyectos.models import Proyecto
from tests.conftest import auth

ENCABEZADO = [
    "Marca temporal",
    "Escribe el nombre oficial o representativo con el que se identifica la iniciativa del proyecto",
    "En una sola frase clara, explica de qué trata el proyecto y qué solución propone",
    "Detalla el contexto, la problemática que busca resolver, la metodología o cómo se llevará a cabo.",
    "Seleccione el área en el que desarrolla su proyecto",
    "Estado actual del proyecto",
    "Nombre del líder o responsable principal del proyecto (debe corresponder a la misma persona titular del correo).",
    "Nombre de coautores separado por coma",
    "Presupuesto estimado o monto gastado en pesos colombianos. Si no requiere fondos ingresa 0",
    "Indica un valor estimado del 0 al 100 según el grado de cumplimiento de los objetivos planteados hasta la fecha",
    "Fecha en que arrancaron formalmente las actividades del proyecto",
    "Fecha prevista para finalizar las fases del proyecto (si aplica)",
    "Selecciona los ODS a los cuales el proyecto aporta de forma directa o indirecta",
    "Describe qué recursos le hacen falta al proyecto para avanzar",
    "Términos clave separados por comas que ayuden a clasificar la temática",
    "Dirección de correo electrónico",
]


def fila(titulo, correo_, *, area="Tecnología", estado="En ejecución", avance=60, lider="Laura Gómez Ruiz",
         coautores="Pedro Díaz", ods="Industria, innovación e infraestructura", resumen=None):
    return [datetime(2026, 11, 17), titulo, resumen or f"Resumen claro del proyecto {titulo}", "Contexto", area, estado,
            lider, coautores, 1000, avance, datetime(2026, 9, 1), None, ods, "Voluntarios", "IoT, agua", correo_]


def excel(*filas):
    libro = Workbook()
    hoja = libro.active
    hoja.append(ENCABEZADO)
    for f in filas:
        hoja.append(f)
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def previa(client, admin, contenido):
    res = client.post("/api/admin/lote/previa", headers=admin,
                      files={"archivo": ("respuestas.xlsx", contenido, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert res.status_code == 200, res.text
    return res.json()


def test_vista_previa_aplica_reglas(client, admin):
    filas = previa(client, admin, excel(
        fila("Plataforma ReforzIA", "lgomezr@ufpso.edu.co", area="Educación", estado="Finalizado", avance=65,
             coautores="Laura Gómez Ruiz, Pedro Díaz", ods="Producción y consumo responsables"),
        fila("AquaRed agua potable", "pdiaz@ufpso.edu.co", estado="En formulación", avance=85,
             ods="Salud y bienestar, Agua limpia y saneamiento"),
    ))
    a, b = filas
    assert a["avance"] == 100 and a["estado"] == "finalizado"
    assert a["ods"] == [4, 12]  # se agregó Educación de calidad
    assert a["equipo"] == ["Pedro Díaz"]  # sin el líder
    assert a["cuenta"] == "nueva" and a["errores"] == []
    assert b["avance"] == 35 and b["ods"] == [3, 6]
    # El correo es de Pedro (coautor), no de la líder: la cuenta lleva su nombre y la líder sigue siendo Laura.
    assert b["nombre_cuenta"] == "Pedro Díaz" and b["lider"] == "Laura Gómez Ruiz"


def test_errores_bloquean_la_confirmacion(client, admin, db):
    filas = previa(client, admin, excel(
        fila("Proyecto con área rara", "a1@ufpso.edu.co", area="Astronomía"),
        fila("Proyecto con correo personal", "alguien@gmail.com"),
        fila("Proyecto resumen largo", "a3@ufpso.edu.co", resumen="x" * 301),
    ))
    assert any("no existe" in e for e in filas[0]["errores"])
    assert any("institucional" in e for e in filas[1]["errores"])
    assert any("301 caracteres" in e for e in filas[2]["errores"])
    res = client.post("/api/admin/lote/confirmar", headers=admin, json=filas)
    assert res.status_code == 422
    assert db.query(Proyecto).count() == 0

    # Corregidas en la vista previa (o excluidas), sí se cargan.
    filas[0]["area"] = "Tecnología"
    filas[1]["incluir"] = False
    filas[2]["resumen"] = "Resumen corto y correcto"
    revisadas = client.post("/api/admin/lote/revisar", headers=admin, json=filas).json()
    assert all(not f["errores"] for f in revisadas if f["incluir"])
    assert client.post("/api/admin/lote/confirmar", headers=admin, json=revisadas).status_code == 200
    assert db.query(Proyecto).count() == 2


def test_confirmar_crea_cuentas_y_un_solo_correo(client, admin, db, estudiante):
    correo.enviados.clear()
    filas = previa(client, admin, excel(
        fila("Sistema hospitalario", "nueva@ufpso.edu.co", lider="Nora Vega", coautores=""),
        fila("Segundo proyecto de Nora", "nueva@ufpso.edu.co", lider="Nora Vega", coautores=""),
        fila("Proyecto de Ana", "ana@ufpso.edu.co"),
        fila("Proyecto de Ana", "otra@ufpso.edu.co"),  # título repetido en el archivo
    ))
    assert filas[2]["cuenta"] == "existente"
    assert any("se repite" in e for e in filas[3]["errores"])
    filas[3]["incluir"] = False
    res = client.post("/api/admin/lote/confirmar", headers=admin, json=filas)
    assert res.status_code == 200, res.text
    assert res.json() == {"proyectos": 3, "cuentas_nuevas": 1, "cuentas_existentes": 1, "correos": 2}

    nora = db.query(Usuario).filter_by(email="nueva@ufpso.edu.co").one()
    assert nora.verificado and nora.rol == "estudiante" and nora.nombre == "Nora Vega"
    assert db.query(Proyecto).filter_by(creado_por_id=nora.id).count() == 2
    # Ni avisos de la campana ni correos de XP/insignias: solo el correo de la carga.
    assert db.query(Notificacion).count() == 0
    para = sorted(c.para for c in correo.enviados)
    assert para == ["ana@ufpso.edu.co", "nueva@ufpso.edu.co"]
    mensaje_nora = next(c for c in correo.enviados if c.para == "nueva@ufpso.edu.co")
    assert "7 días" in mensaje_nora.texto and "Segundo proyecto de Nora" in mensaje_nora.texto
    assert "te pertenece" in next(c for c in correo.enviados if c.para == "ana@ufpso.edu.co").texto

    # El enlace sirve para elegir la contraseña (y una sola vez).
    token = mensaje_nora.texto.split("token=")[1].split()[0]
    assert client.post("/api/auth/restablecer", json={"token": token, "password": "Nueva-Clave1"}).status_code == 200
    assert client.post("/api/auth/restablecer", json={"token": token, "password": "Otra-Clave2"}).status_code == 400
    auth(client, "nueva@ufpso.edu.co", "Nueva-Clave1")

    # Volver a cargar el mismo archivo no duplica: los títulos ya existen.
    again = previa(client, admin, excel(fila("Sistema hospitalario", "nueva@ufpso.edu.co")))
    assert any("Ya hay un proyecto" in e for e in again[0]["errores"])


def test_solo_admin(client, estudiante):
    res = client.post("/api/admin/lote/previa", headers=estudiante,
                      files={"archivo": ("r.xlsx", excel(), "application/octet-stream")})
    assert res.status_code == 403


def test_archivo_sin_columnas(client, admin):
    res = client.post("/api/admin/lote/previa", headers=admin, files={"archivo": ("r.xlsx", b"no es excel", "x")})
    assert res.status_code == 400
