import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, select

from app.core.deps import DbSession, UsuarioActual, requiere
from app.modules.alianzas.models import Miembro
from app.modules.insignias import servicio as insignias
from app.modules.insignias.schemas import InsigniaBreve
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.schemas import ProyectoSalida
from app.modules.roles.servicio import permisos_de
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UsuarioActualizar, UsuarioPropio, UsuarioPublico

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


def propio(db, usuario: Usuario) -> UsuarioPropio:
    salida = UsuarioPropio.model_validate(usuario)
    salida.permisos = sorted(permisos_de(db, usuario))
    return salida


@router.get("/yo", response_model=UsuarioPropio)
def leer_yo(usuario: UsuarioActual, db: DbSession):
    from app.modules.experiencia.servicio import tarea_periodica_ingreso

    tarea_periodica_ingreso(db, usuario)  # XP por entrar (una vez al día)
    return propio(db, usuario)


@router.patch("/yo", response_model=UsuarioPropio)
def actualizar_yo(datos: UsuarioActualizar, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)
    from app.modules.experiencia.servicio import sumar
    from app.modules.insignias.servicio import _perfil_completo

    if _perfil_completo(db, usuario, None):
        sumar(db, usuario, "perfil_completo", "perfil", tareas=tareas)
    insignias.evaluar(db, usuario, tareas)  # p. ej. «Perfil completo»
    db.commit()
    db.refresh(usuario)
    return propio(db, usuario)


@router.get("", response_model=list[UsuarioPublico], dependencies=[Depends(requiere("usuarios.ver"))])
def listar_usuarios(
    db: DbSession,
    rol: str | None = None,
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
    return db.scalars(stmt.order_by(Usuario.nombre).limit(limit).offset(offset)).unique().all()


def _publico(db, usuario_id: uuid.UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioPublico)
def leer_usuario(usuario_id: uuid.UUID, db: DbSession, yo: UsuarioActual):
    # Quien responde una solicitud siempre puede ver a quien la envió, aunque su rol no vea perfiles.
    return _publico(db, usuario_id)


class MiProyectoPublico(BaseModel):
    proyecto: ProyectoSalida
    rol: str  # «Responsable» o el rol con que colabora


class PerfilPublico(BaseModel):
    usuario: UsuarioPublico
    xp: int
    nivel: dict | None  # {id, nombre, icono, color, posicion}
    insignias: list[InsigniaBreve]
    proyectos: list[MiProyectoPublico]


@router.get("/{usuario_id}/perfil", response_model=PerfilPublico, dependencies=[Depends(requiere("usuarios.ver"))])
def perfil_publico(usuario_id: uuid.UUID, db: DbSession):
    """Perfil que ven las demás personas: datos, logros y proyectos donde participa."""
    usuario = _publico(db, usuario_id)
    miembro = {m.proyecto_id: m.rol for m in db.scalars(select(Miembro).where(Miembro.usuario_id == usuario.id))}
    proyectos = db.scalars(select(Proyecto).where(or_(Proyecto.creado_por_id == usuario.id, Proyecto.id.in_(list(miembro))))
                           .order_by(Proyecto.creado_en.desc())).unique()
    from app.modules.experiencia.router import _breve
    from app.modules.experiencia.servicio import niveles_ordenados

    niveles = niveles_ordenados(db)
    nivel = _breve(next((n for n in niveles if n.id == usuario.nivel_id), None), niveles)
    return PerfilPublico(
        usuario=UsuarioPublico.model_validate(usuario), xp=usuario.xp or 0, nivel=nivel.model_dump() if nivel else None,
        insignias=[InsigniaBreve.de(f) for f in insignias.vigentes(db, [usuario.id]).get(usuario.id, [])],
        proyectos=[MiProyectoPublico(proyecto=ProyectoSalida.de(p), rol="Responsable" if p.creado_por_id == usuario.id
                                     else (miembro.get(p.id) or "Colaborador")) for p in proyectos],
    )
