"""Crea (o promueve) un usuario administrador.

Uso: python -m scripts.create_admin correo@ufpso.edu.co "Nombre Completo"
"""

import getpass
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Usuario
from app.modules.usuarios.models import Rol


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    email, nombre = sys.argv[1].lower(), sys.argv[2]
    with SessionLocal() as db:
        usuario = db.scalar(select(Usuario).where(Usuario.email == email))
        if usuario:
            usuario.rol = Rol.ADMIN
            usuario.verificado = True
            print(f"{email} ahora es administrador")
        else:
            password = getpass.getpass("Contraseña: ")
            db.add(Usuario(email=email, nombre=nombre, hashed_password=hash_password(password),
                           rol=Rol.ADMIN, habilidades=[], intereses=[], verificado=True))
            print(f"Administrador {email} creado")
        db.commit()


if __name__ == "__main__":
    main()
