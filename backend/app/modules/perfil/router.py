"""Mi perfil: mis datos, los proyectos donde participo y mis alianzas, en una sola consulta."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.models import Miembro
from app.modules.alianzas.router import solicitudes_de
from app.modules.alianzas.schemas import SolicitudSalida
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.schemas import ProyectoSalida
from app.modules.usuarios.schemas import UsuarioPropio

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


class MiProyecto(BaseModel):
    proyecto: ProyectoSalida
    mi_rol: Literal["responsable", "colaborador"]


class Resumen(BaseModel):
    proyectos: int
    colaboraciones: int  # proyectos ajenos donde soy miembro
    alianzas_activas: int  # personas aceptadas en mis proyectos + proyectos donde me aceptaron
    por_responder: int


class Perfil(BaseModel):
    usuario: UsuarioPropio
    resumen: Resumen
    proyectos: list[MiProyecto]
    alianzas: list[SolicitudSalida]


@router.get("", response_model=Perfil)
def mi_perfil(usuario: UsuarioActual, db: DbSession):
    miembro_de = set(db.scalars(select(Miembro.proyecto_id).where(Miembro.usuario_id == usuario.id)))
    proyectos = db.scalars(
        select(Proyecto).where(or_(Proyecto.creado_por_id == usuario.id, Proyecto.id.in_(miembro_de)))
        .order_by(Proyecto.creado_en.desc(), Proyecto.actualizado_en.desc())
    ).unique()
    mios = [
        MiProyecto(proyecto=ProyectoSalida.de(p), mi_rol="responsable" if p.creado_por_id == usuario.id else "colaborador")
        for p in proyectos
    ]
    alianzas = [SolicitudSalida.de(s, usuario.id) for s in solicitudes_de(db, usuario.id)]
    propios = [m.proyecto.id for m in mios if m.mi_rol == "responsable"]
    miembros_en_mios = len(db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id.in_(propios))).all())
    return Perfil(
        usuario=UsuarioPropio.model_validate(usuario),
        resumen=Resumen(
            proyectos=len(mios),
            colaboraciones=len(miembro_de),
            alianzas_activas=miembros_en_mios + len(miembro_de),
            por_responder=sum(1 for a in alianzas if a.por_responder),
        ),
        proyectos=mios,
        alianzas=alianzas,
    )
