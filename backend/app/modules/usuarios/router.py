import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_, select

from app.core.deps import DbSession, UsuarioActual
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import UsuarioActualizar, UsuarioPropio, UsuarioPublico

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


@router.get("/yo", response_model=UsuarioPropio)
def leer_yo(usuario: UsuarioActual):
    return usuario


@router.patch("/yo", response_model=UsuarioPropio)
def actualizar_yo(datos: UsuarioActualizar, usuario: UsuarioActual, db: DbSession):
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("", response_model=list[UsuarioPublico])
def listar_usuarios(
    db: DbSession,
    _: UsuarioActual,
    rol: Rol | None = None,
    q: str | None = Query(default=None, description="Busca en nombre y programa"),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    stmt = select(Usuario).where(Usuario.activo.is_(True))
    if rol:
        stmt = stmt.where(Usuario.rol == rol)
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(Usuario.nombre.ilike(patron), Usuario.programa.ilike(patron)))
    return db.scalars(stmt.order_by(Usuario.nombre).limit(limit).offset(offset)).all()


@router.get("/{usuario_id}", response_model=UsuarioPublico)
def leer_usuario(usuario_id: uuid.UUID, db: DbSession, _: UsuarioActual):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario
