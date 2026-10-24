from sqlalchemy.orm import Session

from app.modules.admin.models import RegistroAdmin
from app.modules.usuarios.models import Usuario


def registrar(db: Session, admin: Usuario, accion: str, objeto: str, detalle: str = "") -> None:
    """Anota una acción de administración (quien llama hace commit)."""
    db.add(RegistroAdmin(admin_id=admin.id, accion=accion, objeto=objeto[:250], detalle=detalle))
