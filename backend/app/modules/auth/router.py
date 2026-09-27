from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.schemas import Registro, Token
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import UsuarioPropio

router = APIRouter(prefix="/api/auth", tags=["autenticación"])


@router.post("/registro", response_model=UsuarioPropio, status_code=status.HTTP_201_CREATED)
def registrar(datos: Registro, db: DbSession):
    email = datos.email.lower()
    if datos.rol == Rol.ADMIN:
        raise HTTPException(status_code=400, detail="No se puede registrar un administrador")
    dominios = get_settings().allowed_domains
    # Los aliados externos no tienen correo institucional; su verificación queda pendiente de definir.
    if dominios and datos.rol != Rol.ALIADO and email.rsplit("@", 1)[1] not in dominios:
        raise HTTPException(status_code=400, detail="Usa tu correo institucional")
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    usuario = Usuario(
        email=email,
        hashed_password=hash_password(datos.password),
        nombre=datos.nombre,
        rol=datos.rol,
        programa=datos.programa,
        habilidades=[],
        intereses=[],
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    usuario = db.scalar(select(Usuario).where(Usuario.email == form.username.lower()))
    if usuario is None or not usuario.activo or not verify_password(form.password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return Token(access_token=create_access_token(str(usuario.id)))
