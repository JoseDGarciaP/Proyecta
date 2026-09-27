"""Importa todos los modelos para que Alembic y las pruebas vean el esquema completo."""

from app.core.database import Base
from app.modules.actores.models import Actor
from app.modules.alianzas.models import Miembro, Solicitud
from app.modules.catalogo.models import Area, Ods
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.similitud.models import Embedding
from app.modules.usuarios.models import Usuario

__all__ = ["Base", "Actor", "Area", "Embedding", "Miembro", "Ods", "Oportunidad", "Proyecto", "Solicitud", "Usuario"]
