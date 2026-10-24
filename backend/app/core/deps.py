import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.usuarios.models import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    sub = decode_access_token(token)
    try:
        usuario = db.get(Usuario, uuid.UUID(sub)) if sub else None
    except ValueError:
        usuario = None
    if usuario is None or not usuario.activo:
        raise credenciales_invalidas
    if not usuario.verificado:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Confirma tu correo para continuar")
    return usuario


UsuarioActual = Annotated[Usuario, Depends(get_current_user)]


def requiere(*permisos: str):
    """Dependencia: exige que el rol de quien llama tenga todos estos permisos."""

    def dependencia(usuario: UsuarioActual, db: DbSession) -> Usuario:
        from app.modules.roles.servicio import exigir

        for permiso in permisos:
            exigir(db, usuario, permiso)
        return usuario

    return dependencia


def requiere_panel(usuario: UsuarioActual, db: DbSession) -> Usuario:
    """Entrar al panel de administración: cualquier permiso admin.*."""
    from app.modules.roles.servicio import permisos_de

    if not any(p.startswith("admin.") for p in permisos_de(db, usuario)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tu rol no tiene acceso a la administración")
    return usuario


# Quien ejecuta una acción de administración. El permiso concreto lo exige el router o la ruta.
Admin = Annotated[Usuario, Depends(get_current_user)]
