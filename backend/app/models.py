"""Importa todos los modelos para que Alembic y las pruebas vean el esquema completo."""

from app.core.database import Base
from app.modules.actores.models import Actor
from app.modules.catalogo.models import Area, Ods
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario

__all__ = ["Base", "Actor", "Area", "Ods", "Oportunidad", "Proyecto", "Usuario"]
