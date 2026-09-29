import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models import Area, Base, Ods, Usuario
from app.modules.catalogo.seed import AREAS, ODS
from app.modules.usuarios.models import Rol


@pytest.fixture
def db():
    """SQLite en memoria; con TEST_DATABASE_URL corre sobre PostgreSQL (se borra y recrea el esquema)."""
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        engine = create_engine(url)
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.drop_all(engine)
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    session.add_all([Area(nombre=n) for n in AREAS] + [Ods(id=i, nombre=n) for i, n in ODS])
    session.commit()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def auth(client, email, password="clave-segura"):
    res = client.post("/api/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def registrar(client, email, nombre="Ana Pérez", **extra):
    """Registra y confirma el correo con el enlace del mensaje, como lo haría la persona."""
    res = client.post("/api/auth/registro", json={"email": email, "password": "clave-segura", "nombre": nombre, **extra})
    assert res.status_code == 201, res.text
    assert client.post("/api/auth/verificar", json={"token": token_del_correo(email)}).status_code == 200
    return auth(client, email)


def token_del_correo(email):
    from app.core import correo

    mensaje = next(c for c in reversed(correo.enviados) if c.para == email)
    return mensaje.texto.split("token=")[1].split()[0]


@pytest.fixture
def estudiante(client):
    return registrar(client, "ana@ufpso.edu.co")


@pytest.fixture
def admin(client, db):
    db.add(Usuario(email="admin@ufpso.edu.co", hashed_password=hash_password("clave-segura"),
                   nombre="Admin", rol=Rol.ADMIN, habilidades=[], intereses=[], verificado=True))
    db.commit()
    return auth(client, "admin@ufpso.edu.co")


@pytest.fixture(autouse=True)
def ia_sin_modelo(monkeypatch):
    """Las pruebas no llaman a Ollama ni a Claude salvo que lo configuren explícitamente."""
    from app.core.config import Settings
    from app.modules.ia import servicio
    from app.modules.similitud import codificador

    monkeypatch.setattr(servicio, "get_settings", lambda: Settings(ia_proveedor="reglas"))
    # Sin modelo de embeddings: similitud léxica, salvo que la prueba use `embeddings_falsos`.
    monkeypatch.setattr(codificador, "get_settings", lambda: Settings(embeddings_activos=False))
    # Nunca enviar correos reales desde las pruebas.
    from app.core import correo

    monkeypatch.setattr(correo, "get_settings", lambda: Settings(smtp_host=""))
    correo.enviados.clear()


class CodificadorFalso:
    """Vectores por temas: suficiente para comprobar el orden sin descargar el modelo real.

    Cada dimensión es un tema; un texto suma 1 en cada tema cuyas palabras menciona.
    Así «acueducto» y «agua potable» quedan cerca aunque no compartan palabras.
    """

    nombre = "falso-temas"
    TEMAS = [
        {"agua", "acueducto", "riego", "hidrico", "potable", "cuenca"},
        {"salud", "telemedicina", "hospital", "paciente", "medico"},
        {"software", "programacion", "python", "datos", "web", "app"},
        {"agro", "cultivo", "cacao", "campesino", "agroindustria", "suelo"},
        {"energia", "solar", "panel", "electrica"},
        {"educacion", "escuela", "docente", "pedagogia", "ninos"},
    ]

    def __init__(self):
        self.llamadas = 0

    def codificar(self, textos):
        from app.modules.similitud.textos import palabras

        self.llamadas += 1
        salida = []
        for t in textos:
            p = palabras(t)
            v = [float(len(p & palabras(' '.join(tema)))) for tema in self.TEMAS] + [0.1]
            n = sum(x * x for x in v) ** 0.5
            salida.append([x / n for x in v])
        return salida


@pytest.fixture
def embeddings_falsos(monkeypatch):
    from app.modules.similitud import codificador

    falso = CodificadorFalso()
    monkeypatch.setattr(codificador, "reemplazo", falso)
    return falso
