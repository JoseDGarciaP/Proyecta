"""Importa todos los modelos para que Alembic y las pruebas vean el esquema completo."""

from app.core.database import Base
from app.modules.actores.models import Actor
from app.modules.admin.models import RegistroAdmin
from app.modules.alianzas.models import Miembro, Solicitud
from app.modules.catalogo.models import Area, Ods
from app.modules.evidencias.models import Evidencia
from app.modules.experiencia.models import AccionXP, MovimientoXP, Nivel
from app.modules.insignias.models import Insignia, UsuarioInsignia
from app.modules.postulaciones.models import Postulacion
from app.modules.notificaciones.models import Notificacion
from app.modules.parametros.models import Ajuste, Motivo, Plantilla, TipoAporte
from app.modules.chat.models import Lectura, LecturaSolicitud, Mensaje, MensajeSolicitud
from app.modules.oportunidades.models import Oportunidad
from app.modules.proyectos.models import Proyecto
from app.modules.similitud.models import Embedding
from app.modules.roles.models import RolUsuario
from app.modules.usuarios.models import Usuario

__all__ = ["Base", "Actor", "AccionXP", "Evidencia", "MovimientoXP", "Nivel", "Postulacion", "Insignia", "RolUsuario", "UsuarioInsignia", "Ajuste", "Motivo", "Notificacion", "Plantilla", "RegistroAdmin", "TipoAporte", "Area", "Embedding", "Lectura", "LecturaSolicitud", "Mensaje", "MensajeSolicitud", "Miembro", "Ods", "Oportunidad", "Proyecto", "Solicitud", "Usuario"]
