"""Reglas de los aliados externos: la cuenta espera la aprobación de un administrador."""

from sqlalchemy.orm import Session

from app.modules.aliados.models import EstadoAliado, PerfilAliado
from app.modules.usuarios.models import Usuario

PENDIENTE = ("Tu cuenta de aliado está pendiente de aprobación. Un administrador revisará tus datos "
             "y te avisaremos por correo.")


def bloqueo(db: Session, usuario: Usuario) -> str | None:
    """Mensaje si la cuenta es de un aliado que aún no puede ingresar; None si puede.

    Las cuentas de aliado creadas antes de esta regla (sin perfil) o por un administrador siguen entrando.
    """
    perfil = db.get(PerfilAliado, usuario.id)
    if perfil is None or perfil.estado == EstadoAliado.APROBADO:
        return None
    if perfil.estado == EstadoAliado.RECHAZADO:
        return f"Tu registro como aliado fue rechazado. Motivo: {perfil.motivo_rechazo}"
    return PENDIENTE
