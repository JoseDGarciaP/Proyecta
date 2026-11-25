from datetime import date, timedelta

from app.models import Embedding
from tests.conftest import APRUEBA, RECO, registrar
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

    res = client.get(f"/api/ia/proyectos/{base}/similares", headers=estudiante).json()
    assert res["metodo"] == "semantico"
    assert [r["id"] for r in res["resultados"]] == [agua]  # salud queda por debajo del umbral
    assert db.query(Embedding).count() == 3

    # Los vectores se reutilizan: una segunda consulta no vuelve a codificar nada
    llamadas = embeddings_falsos.llamadas
    client.get(f"/api/ia/proyectos/{base}/similares", headers=estudiante)
    assert embeddings_falsos.llamadas == llamadas

    # Si el texto cambia, solo ese vector se recalcula
    client.patch(f"/api/proyectos/{agua}", json={"titulo": "Energía solar escolar", "resumen": "Paneles solares para la escuela de la vereda."}, headers=estudiante)
    assert client.get(f"/api/ia/proyectos/{base}/similares", headers=estudiante).json()["resultados"] == []
    assert embeddings_falsos.llamadas == llamadas + 1


def test_similares_sin_modelo_usa_palabras(client, estudiante):
    base = _crear(client, estudiante)
    otro = _crear(client, estudiante, titulo="Riego por goteo para cacao", etiquetas=["agua"],
                  resumen="Riego automático por goteo para productores de cacao.")
    res = client.get(f"/api/ia/proyectos/{base}/similares", headers=estudiante).json()
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
    sid = client.post(f"/api/proyectos/{pid}/solicitudes", json=RECO, headers=dev).json()["id"]
    client.post(f"/api/alianzas/{sid}/aceptar", json=APRUEBA, headers=estudiante)
    assert client.get(f"/api/ia/proyectos/{pid}/colaboradores", headers=estudiante).json()["resultados"] == []


def test_busqueda_semantica_de_oportunidades(client, admin, embeddings_falsos):
    agua = _oportunidad(client, admin, "Fondo de acueductos rurales", "Financia sistemas de agua potable.", ["Ambiente"])
    _oportunidad(client, admin, "Mentoría para apps", "Acompañamiento a startups de software.", ["Tecnología"])

    res = client.get("/api/ia/buscar", params={"q": "necesito plata para un proyecto de riego"}, headers=admin).json()
    assert res["metodo"] == "semantico"
    assert [r["id"] for r in res["resultados"]] == [agua]  # «riego» ≈ «acueducto» sin palabras en común


def test_para_mi(client, estudiante, admin, embeddings_falsos):
    _crear(client, estudiante)  # proyecto propio: no se sugiere a sí mismo
    op = _oportunidad(client, admin, "Convocatoria de riego", "Riego y agua para el campo.", ["Agroindustria"])
    luis = _con_perfil(client, "luis@ufpso.edu.co", "Luis", habilidades=["riego"], intereses=["agua potable"])
    ajeno = client.get("/api/proyectos", headers=estudiante).json()[0]["id"]

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
    recs = client.post(f"/api/ia/proyectos/{pid}/analisis", headers=estudiante).json()["recomendaciones"]
    assert [r["oportunidad_id"] for r in recs] == [op]
    assert "se parece" in recs[0]["razon"]


def test_estado_informa_embeddings(client, estudiante):
    emb = client.get("/api/ia/estado", headers=estudiante).json()["embeddings"]
    assert emb["activos"] is False and emb["modelo"]


def test_colaboradores_suman_habilidades_requeridas_y_excluyen_inactivos(client, estudiante, admin):
    """Ep5-Hu2: la coincidencia directa de habilidades pesa en el puntaje y las cuentas inactivas no salen."""
    pid = _crear(client, estudiante, necesidades="Buscamos apoyo en Python, Docker y PostgreSQL.", etiquetas=["datos"])
    tres = _con_perfil(client, "tres@ufpso.edu.co", "Tres Habilidades", habilidades=["Python", "Docker", "PostgreSQL"])
    _con_perfil(client, "una@ufpso.edu.co", "Una Habilidad", habilidades=["Python", "fotografía", "dibujo"])
    _con_perfil(client, "nada@ufpso.edu.co", "Sin Coincidencia", habilidades=["cocina"], intereses=["música"])

    res = client.get(f"/api/ia/proyectos/{pid}/colaboradores", headers=estudiante).json()
    titulos = [r["titulo"] for r in res["resultados"]]
    assert titulos[:2] == ["Tres Habilidades", "Una Habilidad"]
    assert "Sin Coincidencia" not in titulos
    assert "Docker, PostgreSQL, Python" in res["resultados"][0]["razon"]

    # Una cuenta desactivada desaparece de las sugerencias
    tres_id = client.get("/api/usuarios/yo", headers=tres).json()["id"]
    assert client.patch(f"/api/admin/usuarios/{tres_id}", json={"activo": False}, headers=admin).status_code == 200
    res = client.get(f"/api/ia/proyectos/{pid}/colaboradores", headers=estudiante).json()
    assert "Tres Habilidades" not in [r["titulo"] for r in res["resultados"]]


def test_similitudes_no_aplica_umbral():
    """`similitudes()` devuelve también los valores bajo el umbral: antes llegaban como 0 y
    colaboradores sugeridos perdía la parte de similitud (70 %) de quien estaba cerca del corte."""
    import uuid
    from types import SimpleNamespace

    from app.modules.similitud.servicio import MINIMO, similitudes

    consulta = "riego agua sensores cultivo cebolla finca productor humedad suelo temperatura plataforma web"
    lejano = SimpleNamespace(id=uuid.uuid4(), t="agua potable escuela rural niños comedor transporte biblioteca deporte música danza teatro pintura cocina idioma lectura")
    sims, metodo = similitudes(None, consulta, "usuario", [lejano], lambda c: c.t)
    assert metodo == "lexico"
    assert 0 < sims[lejano.id] < MINIMO["lexico"]


def test_similares_premia_area_y_etiquetas(client, estudiante, embeddings_falsos):
    """Con texto igual de parecido, gana el que comparte etiquetas; sin ellas hace falta más texto."""
    from app.modules.ia.router import UMBRAL_SIMILARES, puntaje_similar
    from types import SimpleNamespace

    base = SimpleNamespace(area_id=1, etiquetas=["IoT", "sensores"])
    afin = SimpleNamespace(area_id=2, etiquetas=["sensores de suelo", "IoT"])
    misma_area = SimpleNamespace(area_id=1, etiquetas=["educación"])
    assert puntaje_similar(base, afin, 0.45) > puntaje_similar(base, misma_area, 0.45)
    assert puntaje_similar(base, misma_area, 0.45) < UMBRAL_SIMILARES <= puntaje_similar(base, afin, 0.45)
