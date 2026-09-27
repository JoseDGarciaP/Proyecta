from datetime import date, timedelta

from app.models import Embedding
from tests.conftest import registrar
from tests.test_proyectos import PROYECTO


def _crear(client, headers, **cambios):
    res = client.post("/api/proyectos", json={**PROYECTO, **cambios}, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _con_perfil(client, email, nombre, **perfil):
    headers = registrar(client, email, nombre=nombre)
    assert client.patch("/api/usuarios/yo", json=perfil, headers=headers).status_code == 200
    return headers


def _oportunidad(client, admin, titulo, descripcion, areas):
    datos = {"titulo": titulo, "entidad": "Gobernación", "tipo": "financiacion", "descripcion": descripcion,
             "cierra_en": str(date.today() + timedelta(days=30)), "areas": areas}
    return client.post("/api/oportunidades", json=datos, headers=admin).json()["id"]


def test_proyectos_similares_semanticos(client, estudiante, embeddings_falsos, db):
    base = _crear(client, estudiante)  # riego y agua
    agua = _crear(client, estudiante, titulo="Acueducto veredal comunitario", etiquetas=[],
                  resumen="Potabilizar el acueducto de la vereda con filtros de bajo costo.", area="Ambiente")
    _crear(client, estudiante, titulo="Telemedicina rural", etiquetas=["salud"], area="Salud",
           resumen="Consultas por telemedicina para pacientes de puestos de salud.")

    res = client.get(f"/api/ia/proyectos/{base}/similares").json()
    assert res["metodo"] == "semantico"
    assert [r["id"] for r in res["resultados"]] == [agua]  # salud queda por debajo del umbral
    assert db.query(Embedding).count() == 3

    # Los vectores se reutilizan: una segunda consulta no vuelve a codificar nada
    llamadas = embeddings_falsos.llamadas
    client.get(f"/api/ia/proyectos/{base}/similares")
    assert embeddings_falsos.llamadas == llamadas

    # Si el texto cambia, solo ese vector se recalcula
    client.patch(f"/api/proyectos/{agua}", json={"titulo": "Energía solar escolar", "resumen": "Paneles solares para la escuela de la vereda."}, headers=estudiante)
    assert client.get(f"/api/ia/proyectos/{base}/similares").json()["resultados"] == []
    assert embeddings_falsos.llamadas == llamadas + 1


def test_similares_sin_modelo_usa_palabras(client, estudiante):
    base = _crear(client, estudiante)
    otro = _crear(client, estudiante, titulo="Riego por goteo para cacao", etiquetas=["agua"],
                  resumen="Riego automático por goteo para productores de cacao.")
    res = client.get(f"/api/ia/proyectos/{base}/similares").json()
    assert res["metodo"] == "lexico"
    assert res["resultados"][0]["id"] == otro


def test_colaboradores_por_perfil(client, estudiante, embeddings_falsos):
    pid = _crear(client, estudiante, necesidades="Buscamos quien sepa de programación en Python y datos.")
    dev = _con_perfil(client, "dev@ufpso.edu.co", "Dev Python", programa="Ingeniería de Sistemas",
                      habilidades=["Python", "análisis de datos"])
    _con_perfil(client, "med@ufpso.edu.co", "Médica", programa="Enfermería", habilidades=["atención al paciente"])
    registrar(client, "vacio@ufpso.edu.co", nombre="Perfil Vacío")

    res = client.get(f"/api/ia/proyectos/{pid}/colaboradores", headers=estudiante).json()
    assert [r["titulo"] for r in res["resultados"]] == ["Dev Python"]
    assert "Python" in res["resultados"][0]["razon"]

    # Quien ya es miembro no se sugiere
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json={}, headers=dev).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json={}, headers=estudiante)
    assert client.get(f"/api/ia/proyectos/{pid}/colaboradores", headers=estudiante).json()["resultados"] == []


def test_busqueda_semantica_de_oportunidades(client, admin, embeddings_falsos):
    agua = _oportunidad(client, admin, "Fondo de acueductos rurales", "Financia sistemas de agua potable.", ["Ambiente"])
    _oportunidad(client, admin, "Mentoría para apps", "Acompañamiento a startups de software.", ["Tecnología"])

    res = client.get("/api/ia/buscar", params={"q": "necesito plata para un proyecto de riego"}).json()
    assert res["metodo"] == "semantico"
    assert [r["id"] for r in res["resultados"]] == [agua]  # «riego» ≈ «acueducto» sin palabras en común


def test_para_mi(client, estudiante, admin, embeddings_falsos):
    _crear(client, estudiante)  # proyecto propio: no se sugiere a sí mismo
    op = _oportunidad(client, admin, "Convocatoria de riego", "Riego y agua para el campo.", ["Agroindustria"])
    luis = _con_perfil(client, "luis@ufpso.edu.co", "Luis", habilidades=["riego"], intereses=["agua potable"])
    ajeno = client.get("/api/proyectos").json()[0]["id"]

    sug = client.get("/api/ia/para-mi", headers=luis).json()
    assert sug["perfil_completo"] is True
    assert [p["id"] for p in sug["proyectos"]] == [ajeno]
    assert sug["oportunidades"] == []  # Luis aún no participa en proyectos

    propias = client.get("/api/ia/para-mi", headers=estudiante).json()
    assert propias["proyectos"] == [] and propias["perfil_completo"] is False
    assert [o["id"] for o in propias["oportunidades"]] == [op]


def test_analisis_suma_similitud_semantica(client, estudiante, admin, embeddings_falsos):
    pid = _crear(client, estudiante)
    # Sin área, ODS ni etiquetas en común, pero habla del mismo tema: entra por similitud.
    op = _oportunidad(client, admin, "Programa de acueductos", "Acueducto y agua potable veredal.", ["Energía"])
    _oportunidad(client, admin, "Fondo de software", "Apps web y datos.", ["Tecnología"])
    recs = client.post(f"/api/ia/proyectos/{pid}/analisis").json()["recomendaciones"]
    assert [r["oportunidad_id"] for r in recs] == [op]
    assert "se parece" in recs[0]["razon"]


def test_estado_informa_embeddings(client):
    emb = client.get("/api/ia/estado").json()["embeddings"]
    assert emb["activos"] is False and emb["modelo"]
