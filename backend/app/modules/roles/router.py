from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import Admin, DbSession, get_current_user, requiere
from app.modules.admin.bitacora import registrar
from app.modules.roles import servicio
from app.modules.roles.models import RolUsuario
from app.modules.roles.permisos import ASIGNABLES, PERMISOS, TODOS, nombre
from app.modules.roles.schemas import PermisoSalida, RolBreve, RolEntrada, RolSalida
from app.modules.usuarios.models import Usuario

# Público: los roles que se pueden elegir al registrarse.
publico = APIRouter(prefix="/api/auth", tags=["autenticación"])
# Con sesión: todos los roles (para filtros y nombres).
lectura = APIRouter(prefix="/api/roles", tags=["roles"], dependencies=[Depends(get_current_user)])
# Administración de roles: solo el rol Administrador (permiso admin.roles, que no se puede delegar).
admin = APIRouter(prefix="/api/admin", tags=["administración"], dependencies=[Depends(requiere("admin.roles"))])


def _ordenados(db: Session):
    return db.scalars(select(RolUsuario).order_by(RolUsuario.orden, RolUsuario.nombre)).all()


@publico.get("/roles", response_model=list[RolBreve])
def roles_registro(db: DbSession):
    return [r for r in _ordenados(db) if r.registro_publico and r.clave != servicio.ADMIN]


@lectura.get("", response_model=list[RolBreve])
def listar_roles(db: DbSession):
    return _ordenados(db)


@admin.get("/permisos", response_model=list[PermisoSalida])
def catalogo_permisos():
    return [PermisoSalida(**p.__dict__) for p in PERMISOS]


def _salida(db: Session, r: RolUsuario) -> RolSalida:
    salida = RolSalida.model_validate(r)
    salida.usuarios = db.scalar(select(func.count(Usuario.id)).where(Usuario.rol == r.clave)) or 0
    if r.clave == servicio.ADMIN:
        salida.permisos = sorted(TODOS)
    return salida


@admin.get("/roles", response_model=list[RolSalida])
def roles_admin(db: DbSession):
    return [_salida(db, r) for r in _ordenados(db)]


def _validar_permisos(permisos: list[str]) -> list[str]:
    desconocidos = [p for p in permisos if p not in TODOS]
    if desconocidos:
        raise HTTPException(status_code=422, detail=f"Permisos desconocidos: {', '.join(desconocidos)}")
    no_asignables = [nombre(p) for p in permisos if p not in ASIGNABLES]
    if no_asignables:
        raise HTTPException(status_code=422, detail=f"Solo el rol Administrador puede tener: {', '.join(no_asignables)}")
    return sorted(set(permisos))


def _nombre_libre(db: Session, nombre_rol: str, excepto: str | None = None) -> str:
    nombre_rol = nombre_rol.strip()
    existe = db.scalar(select(RolUsuario.clave).where(func.lower(RolUsuario.nombre) == nombre_rol.lower()))
    if existe and existe != excepto:
        raise HTTPException(status_code=409, detail=f"Ya existe el rol «{nombre_rol}»")
    return nombre_rol


@admin.post("/roles", response_model=RolSalida, status_code=status.HTTP_201_CREATED)
def crear_rol(datos: RolEntrada, yo: Admin, db: DbSession):
    nombre_rol = _nombre_libre(db, datos.nombre)
    base, clave, n = servicio.slug(nombre_rol), servicio.slug(nombre_rol), 2
    while db.get(RolUsuario, clave):
        clave = f"{base[:36]}_{n}"
        n += 1
    orden = (db.scalar(select(func.max(RolUsuario.orden))) or 0) + 1
    rol = RolUsuario(clave=clave, nombre=nombre_rol, descripcion=datos.descripcion.strip(), institucional=datos.institucional,
                     registro_publico=datos.registro_publico, permisos=_validar_permisos(datos.permisos), sistema=False, orden=orden)
    db.add(rol)
    registrar(db, yo, "rol.crear", nombre_rol, f"{len(rol.permisos)} permisos")
    db.commit()
    return _salida(db, rol)


@admin.put("/roles/{clave}", response_model=RolSalida)
def editar_rol(clave: str, datos: RolEntrada, yo: Admin, db: DbSession):
    rol = db.get(RolUsuario, clave)
    if rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    antes = set(rol.permisos or [])
    rol.nombre = _nombre_libre(db, datos.nombre, rol.clave)
    rol.descripcion = datos.descripcion.strip()
    if rol.clave == servicio.ADMIN:
        # El Administrador conserva todo y no se registra por la página pública.
        rol.registro_publico = False
    else:
        rol.permisos = _validar_permisos(datos.permisos)
        rol.institucional = datos.institucional
        rol.registro_publico = datos.registro_publico
    despues = set(rol.permisos or [])
    cambios = [f"+{nombre(p)}" for p in sorted(despues - antes)] + [f"−{nombre(p)}" for p in sorted(antes - despues)]
    registrar(db, yo, "rol.editar", rol.nombre, "; ".join(cambios) or "datos del rol")
    db.commit()
    return _salida(db, rol)


@admin.delete("/roles/{clave}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(clave: str, yo: Admin, db: DbSession,
                 reasignar_a: str | None = Query(default=None, description="Rol que recibe a las personas que tenían este")):
    rol = db.get(RolUsuario, clave)
    if rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if rol.sistema:
        raise HTTPException(status_code=409, detail="Los roles del sistema no se pueden eliminar; puedes cambiar sus permisos")
    usuarios = db.scalar(select(func.count(Usuario.id)).where(Usuario.rol == clave)) or 0
    if usuarios:
        destino = db.get(RolUsuario, reasignar_a) if reasignar_a else None
        if destino is None or destino.clave == clave:
            raise HTTPException(status_code=409, detail=f"{usuarios} personas tienen este rol: elige a qué rol pasarlas")
        if destino.clave == servicio.ADMIN:
            raise HTTPException(status_code=409, detail="No se puede pasar a nadie a Administrador de forma masiva")
        db.execute(update(Usuario).where(Usuario.rol == clave).values(rol=destino.clave))
    registrar(db, yo, "rol.eliminar", rol.nombre, f"{usuarios} personas pasaron a {reasignar_a}" if usuarios else "")
    db.delete(rol)
    db.commit()
