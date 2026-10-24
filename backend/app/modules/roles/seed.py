"""Roles iniciales. La migración 0008 y las pruebas los cargan; luego el admin edita sus permisos."""

from app.modules.roles.permisos import BASICOS, PERMISOS

ROLES = [
    # (clave, nombre, descripcion, institucional, registro_publico, permisos)
    ("estudiante", "Estudiante", "Estudiantes con correo institucional.", True, True, BASICOS),
    ("docente", "Docente", "Docentes con correo institucional.", True, True, BASICOS),
    ("administrativo", "Administrativo", "Personal administrativo con correo institucional.", True, True, BASICOS),
    ("aliado", "Aliado externo", "Empresas, entidades y comunidades. Pueden usar su correo personal.", False, True, BASICOS),
    ("admin", "Administrador", "Acceso total a la plataforma y a su configuración.", True, False, [p.clave for p in PERMISOS]),
]


def sembrar(db) -> None:
    from sqlalchemy import func, select

    from app.modules.roles.models import RolUsuario

    if not db.scalar(select(func.count(RolUsuario.clave))):
        db.add_all([
            RolUsuario(clave=c, nombre=n, descripcion=d, institucional=i, registro_publico=r, permisos=list(p),
                       sistema=True, orden=k)
            for k, (c, n, d, i, r, p) in enumerate(ROLES)
        ])
        db.commit()
