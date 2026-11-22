"""Aliados externos: directorio, perfil propio y verificación por un administrador (Ep4-Hu12 a Hu15)."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import String, cast, or_, select

from app.core.database import utcnow
from app.core.deps import Admin, DbSession, UsuarioActual, requiere
from app.modules.admin.bitacora import registrar
from app.modules.aliados.models import TIPOS_ALIADO, EstadoAliado, PerfilAliado
from app.modules.aliados.schemas import (
    AliadoActualizar, AliadoAdmin, AliadoPropio, AliadoPublico, DocumentoAdmin, ProyectoApoyado, Rechazo,
)
from app.modules.alianzas.models import Miembro
from app.modules.notificaciones.models import TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/aliados", tags=["aliados"])
admin = APIRouter(prefix="/api/admin/aliados", tags=["administración"], dependencies=[Depends(requiere("admin.usuarios"))])


def _propio(p: PerfilAliado) -> AliadoPropio:
    return AliadoPropio(usuario_id=p.usuario_id, razon_social=p.razon_social, tipo=p.tipo, documento=p.documento,
                        telefono=p.telefono, sector=p.sector, sitio_web=p.sitio_web, descripcion=p.descripcion,
                        estado=p.estado.value, motivo_rechazo=p.motivo_rechazo)


def _proyectos(db, usuario_id: uuid.UUID) -> list[ProyectoApoyado]:
    filas = db.execute(select(Proyecto.id, Proyecto.titulo, Miembro.rol).join(Miembro, Miembro.proyecto_id == Proyecto.id)
                       .where(Miembro.usuario_id == usuario_id).order_by(Proyecto.titulo)).all()
    return [ProyectoApoyado(id=i, titulo=t, rol=r or "Aliado") for i, t, r in filas]


@router.get("/tipos", response_model=list[str])
def tipos():
    return TIPOS_ALIADO


@router.get("", response_model=list[AliadoPublico], dependencies=[Depends(requiere("usuarios.ver"))])
def listar(db: DbSession, sector: str | None = None, interes: str | None = None, q: str | None = None,
           limit: int = Query(default=100, le=300)):
    """Directorio de aliados verificados, con filtro por sector y área de interés (Ep4-Hu14)."""
    stmt = (select(PerfilAliado).join(Usuario, Usuario.id == PerfilAliado.usuario_id)
            .where(PerfilAliado.estado == EstadoAliado.APROBADO, Usuario.activo.is_(True)))
    if sector:
        stmt = stmt.where(PerfilAliado.sector.ilike(f"%{sector}%"))
    if interes:
        stmt = stmt.where(cast(Usuario.intereses, String).ilike(f"%{interes}%"))
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(Usuario.nombre.ilike(patron), PerfilAliado.razon_social.ilike(patron),
                              PerfilAliado.descripcion.ilike(patron)))
    return [AliadoPublico(usuario_id=p.usuario_id, nombre=p.usuario.nombre, razon_social=p.razon_social, tipo=p.tipo,
                          sector=p.sector, sitio_web=p.sitio_web, descripcion=p.descripcion,
                          intereses=p.usuario.intereses or [], proyectos=_proyectos(db, p.usuario_id))
            for p in db.scalars(stmt.order_by(PerfilAliado.razon_social).limit(limit)).unique()]


@router.get("/yo", response_model=AliadoPropio | None)
def leer_mio(usuario: UsuarioActual, db: DbSession):
    perfil = db.get(PerfilAliado, usuario.id)
    return _propio(perfil) if perfil else None


@router.put("/yo", response_model=AliadoPropio)
def actualizar_mio(datos: AliadoActualizar, usuario: UsuarioActual, db: DbSession):
    """El aliado cambia teléfono, sector, descripción, sitio web y razón social (Ep4-Hu13)."""
    perfil = db.get(PerfilAliado, usuario.id)
    if perfil is None:
        perfil = PerfilAliado(usuario_id=usuario.id, estado=EstadoAliado.APROBADO)
        db.add(perfil)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        if valor is not None:
            setattr(perfil, campo, valor.strip())
    db.commit()
    return _propio(perfil)


# ---- Administración ---------------------------------------------------------------------------

def _obtener(db, usuario_id: uuid.UUID) -> PerfilAliado:
    perfil = db.get(PerfilAliado, usuario_id)
    if perfil is None:
        raise HTTPException(status_code=404, detail="Aliado no encontrado")
    return perfil


def _admin(p: PerfilAliado) -> AliadoAdmin:
    return AliadoAdmin(**_propio(p).model_dump(), nombre=p.usuario.nombre, email=p.usuario.email,
                       creado_en=p.creado_en, revisado_en=p.revisado_en)


@admin.get("", response_model=list[AliadoAdmin])
def listar_admin(db: DbSession, estado: str | None = Query(default=None, pattern="^(pendiente|aprobado|rechazado)$")):
    stmt = select(PerfilAliado)
    if estado:
        stmt = stmt.where(PerfilAliado.estado == EstadoAliado(estado))
    return [_admin(p) for p in db.scalars(stmt.order_by(PerfilAliado.creado_en.desc())).unique()]


@admin.post("/{usuario_id}/aprobar", response_model=AliadoAdmin)
def aprobar(usuario_id: uuid.UUID, quien: Admin, db: DbSession, tareas: BackgroundTasks):
    perfil = _obtener(db, usuario_id)
    perfil.estado, perfil.motivo_rechazo = EstadoAliado.APROBADO, ""
    perfil.revisado_por_id, perfil.revisado_en = quien.id, utcnow()
    perfil.usuario.rol = "aliado"
    notificar(db, perfil.usuario, TipoNotificacion.CUENTA, "Tu cuenta de aliado fue aprobada",
              "Ya puedes ingresar a Proyecta y apoyar proyectos.", "/ingresar", tareas,
              parrafos=["Un administrador verificó tus datos. Ya puedes ingresar con tu correo y contraseña."],
              boton="Ingresar a Proyecta")
    registrar(db, quien, "aliado.aprobar", f"{perfil.usuario.nombre} <{perfil.usuario.email}>",
              f"{perfil.razon_social} · documento {perfil.documento or '—'}")
    db.commit()
    return _admin(perfil)


@admin.post("/{usuario_id}/rechazar", response_model=AliadoAdmin)
def rechazar(usuario_id: uuid.UUID, datos: Rechazo, quien: Admin, db: DbSession, tareas: BackgroundTasks):
    perfil = _obtener(db, usuario_id)
    motivo = datos.motivo.strip()
    perfil.estado, perfil.motivo_rechazo = EstadoAliado.RECHAZADO, motivo
    perfil.revisado_por_id, perfil.revisado_en = quien.id, utcnow()
    notificar(db, perfil.usuario, TipoNotificacion.CUENTA, "Tu registro como aliado no fue aprobado", f"Motivo: {motivo}",
              "/registro", tareas, parrafos=["Un administrador revisó tu registro y no lo aprobó."],
              detalles=[("Motivo", motivo)], boton="Ir a Proyecta")
    registrar(db, quien, "aliado.rechazar", f"{perfil.usuario.nombre} <{perfil.usuario.email}>", f"Motivo: {motivo}")
    db.commit()
    return _admin(perfil)


@admin.put("/{usuario_id}/documento", response_model=AliadoAdmin)
def cambiar_documento(usuario_id: uuid.UUID, datos: DocumentoAdmin, quien: Admin, db: DbSession):
    """Solo un administrador cambia el NIT o la cédula del aliado (Ep4-Hu13)."""
    perfil = _obtener(db, usuario_id)
    nuevo = datos.documento.strip()
    otro = db.scalar(select(PerfilAliado).where(PerfilAliado.documento == nuevo))
    if otro is not None and otro.usuario_id != perfil.usuario_id:
        raise HTTPException(status_code=409, detail="Ya existe un aliado con ese documento")
    registrar(db, quien, "aliado.documento", perfil.usuario.nombre, f"{perfil.documento or '—'} → {nuevo}")
    perfil.documento = nuevo
    db.commit()
    return _admin(perfil)
