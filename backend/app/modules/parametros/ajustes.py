"""Ajustes generales guardados en la tabla `ajustes`, con valores por defecto si el admin no los ha cambiado."""

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.parametros.models import Ajuste


class Ajustes(BaseModel):
    # Dominios de correo con los que se pueden registrar estudiantes, docentes y administrativos.
    # Vacío = cualquier dominio. Los aliados externos nunca se restringen.
    dominios_permitidos: list[str] = Field(default_factory=list)
    # Interruptores generales de los correos de alerta (cada persona además puede apagarlos en su perfil).
    correo_solicitudes: bool = True  # nueva solicitud o invitación
    correo_respuestas: bool = True  # aprobada, rechazada o cancelada, con el motivo
    correo_mensajes: bool = True  # resumen de mensajes sin leer
    correo_cuenta: bool = True  # cambios hechos por un administrador en la cuenta o en sus proyectos
    correo_logros: bool = True  # insignias ganadas
    # Minutos que debe llevar un mensaje sin leer antes de avisar por correo.
    resumen_espera_minutos: int = Field(default=30, ge=5, le=1440)

    @field_validator("dominios_permitidos")
    @classmethod
    def limpiar(cls, v: list[str]) -> list[str]:
        dominios = []
        for d in v:
            d = d.strip().lower().lstrip("@")
            if not d:
                continue
            if "." not in d or " " in d or "@" in d:
                raise ValueError(f"«{d}» no es un dominio válido")
            dominios.append(d)
        return list(dict.fromkeys(dominios))


def _por_defecto() -> dict:
    return Ajustes(dominios_permitidos=get_settings().allowed_domains).model_dump()


def leer(db: Session) -> Ajustes:
    valores = _por_defecto()
    for fila in db.scalars(select(Ajuste)):
        if fila.clave in valores:
            valores[fila.clave] = fila.valor
    return Ajustes.model_validate(valores)


def guardar(db: Session, ajustes: Ajustes) -> Ajustes:
    for clave, valor in ajustes.model_dump().items():
        fila = db.get(Ajuste, clave)
        if fila is None:
            db.add(Ajuste(clave=clave, valor=valor))
        else:
            fila.valor = valor
    db.commit()
    return leer(db)


def dominio_permitido(db: Session, email: str, rol) -> bool:
    """Estudiantes, docentes, administrativos y admins usan un correo de los dominios permitidos
    (el institucional); los aliados externos pueden usar su correo personal."""
    from app.modules.roles.models import RolUsuario

    dominios = leer(db).dominios_permitidos
    definicion = db.get(RolUsuario, str(getattr(rol, "value", rol)))
    institucional = definicion.institucional if definicion else True
    return not dominios or not institucional or email.rsplit("@", 1)[-1].lower() in dominios


def mensaje_dominio(db: Session) -> str:
    dominios = " o ".join(f"@{d}" for d in leer(db).dominios_permitidos)
    return (f"Estudiantes, docentes y administrativos deben usar un correo institucional {dominios}. "
            "Solo los aliados externos (o los roles que no lo exigen) pueden usar un correo personal.")
