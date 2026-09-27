import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.modules.usuarios.models import Rol, Usuario

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
    return usuario


UsuarioActual = Annotated[Usuario, Depends(get_current_user)]


def require_admin(usuario: UsuarioActual) -> Usuario:
    if usuario.rol != Rol.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere rol de administrador")
    return usuario


Admin = Annotated[Usuario, Depends(require_admin)]
