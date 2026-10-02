import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import correo, validacion_correo
from app.core.config import get_settings
from app.core.deps import DbSession
from app.core.security import create_access_token, create_token, decode_token, hash_password, verify_password
from app.modules.auth import google
from app.modules.auth.schemas import ConfigAuth, IngresoGoogle, Reenvio, Registro, Token, Verificacion
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import UsuarioPropio

router = APIRouter(prefix="/api/auth", tags=["autenticación"])

NO_VERIFICADO = "Confirma tu correo antes de ingresar. Revisa tu bandeja de entrada (y la de spam)."


def _dominio_permitido(email: str, rol: Rol) -> bool:
    dominios = get_settings().allowed_domains
    # Los aliados externos no tienen correo institucional; su verificación queda pendiente de definir.
    return not dominios or rol == Rol.ALIADO or email.rsplit("@", 1)[1] in dominios


def enviar_verificacion(usuario: Usuario, tareas: BackgroundTasks) -> None:
    settings = get_settings()
    token = create_token(str(usuario.id), "verificar", settings.verificacion_horas * 60)
    enlace = f"{settings.frontend_url.rstrip('/')}/verificar?token={token}"
    tareas.add_task(correo.enviar, correo.verificacion(usuario.email, usuario.nombre, enlace, settings.verificacion_horas))


@router.get("/config", response_model=ConfigAuth)
def configuracion():
    """Lo que la interfaz necesita para mostrar el botón de Google."""
    settings = get_settings()
    return ConfigAuth(google_client_id=settings.google_client_id or None, dominios=settings.allowed_domains)


@router.post("/registro", response_model=UsuarioPropio, status_code=status.HTTP_201_CREATED)
def registrar(datos: Registro, db: DbSession, tareas: BackgroundTasks):
    if datos.rol == Rol.ADMIN:
        raise HTTPException(status_code=400, detail="No se puede registrar un administrador")
    email = _validar_correo(datos.email)
    if not _dominio_permitido(email, datos.rol):
        raise HTTPException(status_code=400, detail="Usa tu correo institucional")
    usuario = _buscar(db, email)
    if usuario is not None and usuario.verificado:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    if usuario is None:
        usuario = Usuario(email=email, habilidades=[], intereses=[])
        db.add(usuario)
    # Si la cuenta existía sin confirmar, se reemplazan los datos: nadie puede «apartar» un correo
    # ajeno, porque solo quien abre el buzón puede confirmarlo.
    usuario.hashed_password = hash_password(datos.password)
    usuario.nombre = datos.nombre
    usuario.rol = datos.rol
    usuario.programa = datos.programa
    usuario.verificado = False
    db.commit()
    db.refresh(usuario)
    enviar_verificacion(usuario, tareas)
    return usuario


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    usuario = _buscar(db, form.username.strip().lower())
    if usuario is None or not usuario.activo or not verify_password(form.password, usuario.hashed_password):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    if not usuario.verificado:
        raise HTTPException(status_code=403, detail=NO_VERIFICADO)
    return Token(access_token=create_access_token(str(usuario.id)))


@router.post("/verificar", response_model=Token)
def verificar(datos: Verificacion, db: DbSession):
    """Confirma el correo con el enlace recibido y deja la sesión iniciada."""
    sub = decode_token(datos.token, "verificar")
    usuario_id = _uuid(sub) if sub else None
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=400, detail="El enlace no es válido o ya venció. Pide uno nuevo.")
    usuario.verificado = True
    db.commit()
    return Token(access_token=create_access_token(str(usuario.id)))


@router.post("/reenviar-verificacion", status_code=status.HTTP_202_ACCEPTED)
def reenviar(datos: Reenvio, db: DbSession, tareas: BackgroundTasks):
    """Responde igual exista o no la cuenta, para no revelar qué correos están registrados."""
    usuario = _buscar(db, datos.email.strip().lower())
    if usuario and usuario.activo and not usuario.verificado:
        enviar_verificacion(usuario, tareas)
    return {"detalle": "Si la cuenta existe y falta confirmarla, te enviamos un enlace nuevo."}


@router.post("/google", response_model=Token)
def ingresar_con_google(datos: IngresoGoogle, db: DbSession):
    try:
        cuenta = google.verificar(datos.credential)
    except google.TokenGoogleInvalido as error:
        raise HTTPException(status_code=401, detail=f"No se pudo validar la cuenta de Google: {error}") from error
    email = str(cuenta.get("email", "")).lower()
    if not email or not cuenta.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google no confirmó el correo de esta cuenta")
    if not _dominio_permitido(email, Rol.ESTUDIANTE):
        raise HTTPException(status_code=403, detail="Usa tu cuenta institucional de Google (@ufpso.edu.co)")

    usuario = db.scalar(select(Usuario).where(Usuario.google_sub == cuenta["sub"])) or db.scalar(
        select(Usuario).where(Usuario.email == email))
    if usuario is None:
        usuario = Usuario(
            email=email,
            # Sin contraseña utilizable: entra con Google (o puede pedir una más adelante).
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            nombre=cuenta.get("name") or email.split("@")[0],
            rol=Rol.ESTUDIANTE,
            habilidades=[],
            intereses=[],
            activo=True,
        )
        db.add(usuario)
    if not usuario.activo:
        raise HTTPException(status_code=401, detail="La cuenta está desactivada")
    usuario.google_sub = cuenta["sub"]
    usuario.verificado = True  # Google ya verificó el correo
    db.commit()
    return Token(access_token=create_access_token(str(usuario.id)))


def _validar_correo(email: str) -> str:
    try:
        return validacion_correo.validar(email).email
    except validacion_correo.CorreoNoValido as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _buscar(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email))


def _uuid(valor: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(valor)
    except ValueError:
        return None
