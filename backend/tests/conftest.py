import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = Session()
    session.add_all([Area(nombre=n) for n in AREAS] + [Ods(id=i, nombre=n) for i, n in ODS])
    session.commit()
    yield session
    session.close()


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
    res = client.post("/api/auth/registro", json={"email": email, "password": "clave-segura", "nombre": nombre, **extra})
    assert res.status_code == 201, res.text
    return auth(client, email)


@pytest.fixture
def estudiante(client):
    return registrar(client, "ana@ufpso.edu.co")


@pytest.fixture
def admin(client, db):
    db.add(Usuario(email="admin@ufpso.edu.co", hashed_password=hash_password("clave-segura"),
                   nombre="Admin", rol=Rol.ADMIN, habilidades=[], intereses=[]))
    db.commit()
    return auth(client, "admin@ufpso.edu.co")
