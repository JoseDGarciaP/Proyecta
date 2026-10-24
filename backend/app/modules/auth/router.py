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
from app.core.security import (
    create_access_token,
    create_token,
    decode_payload,
    decode_token,
    hash_password,
    huella_password,
    verify_password,
)
from app.modules.auth import google
from app.modules.parametros import ajustes
from app.modules.auth.schemas import (
    ConfigAuth,
    IngresoGoogle,
    Reenvio,
    Registro,
    Restablecer,
    Token,
    Verificacion,
)
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import UsuarioPropio

router = APIRouter(prefix="/api/auth", tags=["autenticación"])

NO_VERIFICADO = "Confirma tu correo antes de ingresar. Revisa tu bandeja de entrada (y la de spam)."


def _dominio_permitido(db: Session, email: str, rol: str) -> bool:
    return ajustes.dominio_permitido(db, email, rol)


def enviar_verificacion(usuario: Usuario, tareas: BackgroundTasks) -> None:
    settings = get_settings()
    token = create_token(str(usuario.id), "verificar", settings.verificacion_horas * 60)
    enlace = f"{settings.frontend_url.rstrip('/')}/verificar?token={token}"
    tareas.add_task(correo.enviar, correo.verificacion(usuario.email, usuario.nombre, enlace, settings.verificacion_horas))


def enviar_restablecer(usuario: Usuario, tareas: BackgroundTasks, nueva_cuenta: bool = False) -> None:
    """Enlace para elegir contraseña. Con `nueva_cuenta` (la creó un admin) vence en `verificacion_horas`."""
    settings = get_settings()
    minutos = settings.verificacion_horas * 60 if nueva_cuenta else settings.restablecer_minutos
    token = create_token(str(usuario.id), "restablecer", minutos, huella=huella_password(usuario.hashed_password))
    enlace = f"{settings.frontend_url.rstrip('/')}/restablecer?token={token}"
    if nueva_cuenta:
        tareas.add_task(correo.enviar, correo.cuenta_creada(usuario.email, usuario.nombre, enlace, settings.verificacion_horas))
    else:
        tareas.add_task(correo.enviar, correo.restablecer(usuario.email, usuario.nombre, enlace, minutos))


@router.get("/config", response_model=ConfigAuth)
def configuracion(db: DbSession):
    """Lo que la interfaz necesita para mostrar el botón de Google y avisar qué correos se aceptan."""
    settings = get_settings()
    return ConfigAuth(google_client_id=settings.google_client_id or None, dominios=ajustes.leer(db).dominios_permitidos)


@router.post("/registro", response_model=UsuarioPropio, status_code=status.HTTP_201_CREATED)
def registrar(datos: Registro, db: DbSession, tareas: BackgroundTasks):
    from app.modules.roles.models import RolUsuario

    rol = db.get(RolUsuario, datos.rol)
    if rol is None or not rol.registro_publico or rol.clave == Rol.ADMIN:
        raise HTTPException(status_code=400, detail="Ese rol no se puede elegir al registrarse")
    email = validar_correo(datos.email)
    if not _dominio_permitido(db, email, datos.rol):
        raise HTTPException(status_code=400, detail=ajustes.mensaje_dominio(db))
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
    usuario.rol = rol.clave
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


@router.post("/recuperar", status_code=status.HTTP_202_ACCEPTED)
def recuperar(datos: Reenvio, db: DbSession, tareas: BackgroundTasks):
    """Envía el enlace para elegir otra contraseña. Responde igual exista o no la cuenta."""
    usuario = _buscar(db, datos.email.strip().lower())
    if usuario and usuario.activo:
        enviar_restablecer(usuario, tareas)
    return {"detalle": "Si hay una cuenta con ese correo, te enviamos un enlace para cambiar la contraseña."}


@router.post("/restablecer", response_model=Token)
def restablecer(datos: Restablecer, db: DbSession):
    """Cambia la contraseña con el enlace del correo y deja la sesión iniciada."""
    payload = decode_payload(datos.token, "restablecer")
    usuario_id = _uuid(payload["sub"]) if payload else None
    usuario = db.get(Usuario, usuario_id) if usuario_id else None
    # La huella cambia con la contraseña: un enlace ya usado (o anterior a otro cambio) deja de servir.
    if usuario is None or not usuario.activo or payload.get("huella") != huella_password(usuario.hashed_password):
        raise HTTPException(status_code=400, detail="El enlace no es válido, ya se usó o venció. Pide uno nuevo.")
    usuario.hashed_password = hash_password(datos.password)
    usuario.verificado = True  # abrió el enlace desde su buzón: el correo es suyo
    db.commit()
    return Token(access_token=create_access_token(str(usuario.id)))


@router.post("/google", response_model=Token)
def ingresar_con_google(datos: IngresoGoogle, db: DbSession):
    try:
        cuenta = google.verificar(datos.credential)
    except google.TokenGoogleInvalido as error:
        raise HTTPException(status_code=401, detail=f"No se pudo validar la cuenta de Google: {error}") from error
    email = str(cuenta.get("email", "")).lower()
    if not email or not cuenta.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google no confirmó el correo de esta cuenta")
    if not _dominio_permitido(db, email, Rol.ESTUDIANTE):
        dominios = ", ".join(f"@{d}" for d in ajustes.leer(db).dominios_permitidos)
        raise HTTPException(status_code=403, detail=f"Usa tu cuenta institucional de Google ({dominios})")

    usuario = db.scalar(select(Usuario).where(Usuario.google_sub == cuenta["sub"])) or db.scalar(
        select(Usuario).where(Usuario.email == email))
    if usuario is None:
        usuario = Usuario(
            email=email,
            # Sin contraseña utilizable: entra con Google (o puede pedir una más adelante).
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            nombre=cuenta.get("name") or email.split("@")[0],
            rol=Rol.ESTUDIANTE.value,
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


def validar_correo(email: str) -> str:
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
