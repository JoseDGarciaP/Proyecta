import re
import unicodedata

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.roles.models import RolUsuario
from app.modules.roles.permisos import TODOS, nombre

ADMIN = "admin"


def obtener(db: Session, clave: str) -> RolUsuario | None:
    return db.get(RolUsuario, clave)


def permisos_de(db: Session, usuario) -> frozenset[str]:
    """Permisos efectivos. El rol Administrador siempre los tiene todos (no se puede bloquear)."""
    if usuario.rol == ADMIN:
        return TODOS
    cache = getattr(usuario, "_permisos_cache", None)
    if cache is None:
        rol = obtener(db, usuario.rol)
        cache = frozenset(rol.permisos or []) & TODOS if rol else frozenset()
        usuario._permisos_cache = cache
    return cache


def puede(db: Session, usuario, permiso: str) -> bool:
    return permiso in permisos_de(db, usuario)


def exigir(db: Session, usuario, permiso: str) -> None:
    if not puede(db, usuario, permiso):
        raise HTTPException(status_code=403, detail=f"Tu rol no tiene permiso para: {nombre(permiso).lower()}")


def usuarios_con_permiso(db: Session, permiso: str) -> list:
    """Personas activas cuyo rol tiene el permiso (siempre incluye a los Administradores)."""
    from sqlalchemy import select

    from app.modules.usuarios.models import Usuario

    claves = [ADMIN] + [r.clave for r in db.scalars(select(RolUsuario)) if permiso in (r.permisos or [])]
    return list(db.scalars(select(Usuario).where(Usuario.rol.in_(claves), Usuario.activo.is_(True), Usuario.verificado.is_(True))).unique())


def nombre_rol(db: Session, clave: str) -> str:
    rol = obtener(db, clave)
    return rol.nombre if rol else clave


def slug(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")[:40] or "rol"
