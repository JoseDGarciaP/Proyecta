"""Panel de administración: usuarios, catálogos, ajustes, moderación, estadísticas y bitácora.

Todo exige rol de administrador (se aplica a todo el router en main.py).
"""

import secrets
import uuid
from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.core.deps import Admin, DbSession, requiere
from app.core.security import hash_password
from app.modules.actores.models import Actor
from app.modules.admin.bitacora import registrar
from app.modules.admin.models import RegistroAdmin
from app.modules.admin.schemas import (
    AreaAdmin, AreaEntrada, CambiosUsuario, Conteo, Eliminacion, Estadisticas, NuevoUsuario, OdsAdmin, OdsEntrada,
    PaginaUsuarios, ProyectoAdmin, RegistroSalida, ResultadoResumen, UsoMotivo, UsuarioAdmin,
)
from app.modules.alianzas.models import EstadoSolicitud, Miembro, Solicitud
from app.modules.auth.router import enviar_restablecer, validar_correo
from app.modules.catalogo.models import Area, Ods, oportunidad_areas
from app.modules.notificaciones.models import Notificacion, TipoNotificacion
from app.modules.notificaciones.servicio import enviar_resumenes, notificar
from app.modules.oportunidades.models import Oportunidad
from app.modules.parametros import ajustes as ajustes_srv
from app.modules.parametros.models import Motivo, Plantilla, TipoAporte
from app.modules.parametros.schemas import (
    MotivoEntrada, MotivoSalida, PlantillaEntrada, PlantillaSalida, TipoAporteEntrada, TipoAporteSalida,
)
from app.modules.proyectos.models import Proyecto
from app.modules.roles import servicio as roles_srv
from app.modules.roles.models import RolUsuario
from app.modules.usuarios.models import Rol, Usuario

def _seccion(permiso: str) -> APIRouter:
    return APIRouter(prefix="/api/admin", tags=["administración"], dependencies=[Depends(requiere(permiso))])


# Cada sección del panel exige su propio permiso (Administración → Roles y permisos).
r_resumen = _seccion("admin.resumen")
r_usuarios = _seccion("admin.usuarios")
r_catalogos = _seccion("admin.catalogos")
r_colaboracion = _seccion("admin.colaboracion")
r_ajustes = _seccion("admin.ajustes")
r_moderacion = _seccion("admin.moderacion")
r_bitacora = _seccion("admin.bitacora")
routers = [r_resumen, r_usuarios, r_catalogos, r_colaboracion, r_ajustes, r_moderacion, r_bitacora]


# ---- Estadísticas ----------------------------------------------------------------------------

@r_resumen.get("/estadisticas", response_model=Estadisticas)
def estadisticas(db: DbSession):
    contar = lambda stmt: db.scalar(stmt) or 0  # noqa: E731
    por_estado = dict(db.execute(select(Solicitud.estado, func.count()).group_by(Solicitud.estado)).all())
    aceptadas, rechazadas = por_estado.get(EstadoSolicitud.ACEPTADA, 0), por_estado.get(EstadoSolicitud.RECHAZADA, 0)
    motivos = db.execute(
        select(Solicitud.motivo_nombre, Solicitud.estado, func.count())
        .where(Solicitud.motivo_nombre != "").group_by(Solicitud.motivo_nombre, Solicitud.estado)
        .order_by(func.count().desc())
    ).all()
    aportes = db.execute(
        select(Solicitud.rol_propuesto, func.count()).where(Solicitud.rol_propuesto != "")
        .group_by(Solicitud.rol_propuesto).order_by(func.count().desc())
    ).all()
    hace_30 = utcnow() - timedelta(days=30)
    return Estadisticas(
        usuarios_total=contar(select(func.count(Usuario.id))),
        usuarios_activos=contar(select(func.count(Usuario.id)).where(Usuario.activo.is_(True), Usuario.verificado.is_(True))),
        usuarios_sin_verificar=contar(select(func.count(Usuario.id)).where(Usuario.verificado.is_(False))),
        usuarios_inactivos=contar(select(func.count(Usuario.id)).where(Usuario.activo.is_(False))),
        usuarios_por_rol=[Conteo(clave=roles_srv.nombre_rol(db, r), total=n) for r, n in
                          db.execute(select(Usuario.rol, func.count()).group_by(Usuario.rol)).all()],
        proyectos=contar(select(func.count(Proyecto.id))),
        oportunidades_abiertas=contar(select(func.count(Oportunidad.id)).where(Oportunidad.cierra_en >= date.today())),
        actores=contar(select(func.count(Actor.id))),
        solicitudes_por_estado=[Conteo(clave=e.value, total=por_estado.get(e, 0)) for e in EstadoSolicitud],
        tasa_aprobacion=round(aceptadas / (aceptadas + rechazadas), 3) if aceptadas + rechazadas else None,
        motivos=[UsoMotivo(motivo=m, tipo="aprobacion" if e == EstadoSolicitud.ACEPTADA else "rechazo", total=n)
                 for m, e, n in motivos],
        aportes=[Conteo(clave=a, total=n) for a, n in aportes],
        correos_30_dias=contar(select(func.count(Notificacion.id)).where(
            Notificacion.correo_enviado.is_(True), Notificacion.creada_en >= hace_30)),
        notificaciones_sin_leer=contar(select(func.count(Notificacion.id)).where(Notificacion.leida.is_(False))),
    )


# ---- Usuarios --------------------------------------------------------------------------------

def _usuario_admin(db: Session, u: Usuario) -> UsuarioAdmin:
    return UsuarioAdmin(
        id=u.id, email=u.email, nombre=u.nombre, rol=u.rol, rol_nombre=u.rol_nombre, programa=u.programa, activo=u.activo,
        verificado=u.verificado, con_google=bool(u.google_sub), creado_en=u.creado_en,
        proyectos=db.scalar(select(func.count(Proyecto.id)).where(Proyecto.creado_por_id == u.id)) or 0,
        colaboraciones=db.scalar(select(func.count()).where(Miembro.usuario_id == u.id)) or 0,
    )


def _obtener_usuario(db: Session, usuario_id: uuid.UUID) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@r_usuarios.get("/usuarios", response_model=PaginaUsuarios)
def listar_usuarios(
    db: DbSession,
    q: str | None = Query(default=None, description="Busca en nombre, correo y programa"),
    rol: str | None = None,
    estado: str | None = Query(default=None, pattern="^(activo|inactivo|sin_verificar)$"),
    limite: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    stmt = select(Usuario)
    if q:
        patron = f"%{q.strip()}%"
        stmt = stmt.where(or_(Usuario.nombre.ilike(patron), Usuario.email.ilike(patron), Usuario.programa.ilike(patron)))
    if rol:
        stmt = stmt.where(Usuario.rol == rol)
    if estado == "activo":
        stmt = stmt.where(Usuario.activo.is_(True), Usuario.verificado.is_(True))
    elif estado == "inactivo":
        stmt = stmt.where(Usuario.activo.is_(False))
    elif estado == "sin_verificar":
        stmt = stmt.where(Usuario.verificado.is_(False))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    usuarios = db.scalars(stmt.order_by(Usuario.nombre).limit(limite).offset(offset)).unique().all()
    return PaginaUsuarios(total=total, items=[_usuario_admin(db, u) for u in usuarios])


@r_usuarios.post("/usuarios", response_model=UsuarioAdmin, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: NuevoUsuario, admin: Admin, db: DbSession, tareas: BackgroundTasks):
    """Crea la cuenta ya verificada y le envía un enlace para que elija su contraseña.

    Estudiantes, docentes, administrativos y admins: correo institucional. Aliados externos: cualquiera.
    """
    _validar_rol(db, admin, datos.rol)
    email = validar_correo(str(datos.email))  # formato, tipeo, desechables y DNS, igual que el registro
    if not ajustes_srv.dominio_permitido(db, email, datos.rol):
        raise HTTPException(status_code=400, detail=ajustes_srv.mensaje_dominio(db))
    if db.scalar(select(Usuario.id).where(Usuario.email == email)):
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")
    usuario = Usuario(email=email, nombre=datos.nombre, rol=datos.rol, programa=datos.programa,
                      hashed_password=hash_password(secrets.token_urlsafe(32)), habilidades=[], intereses=[],
                      verificado=True, activo=True)
    db.add(usuario)
    db.flush()
    registrar(db, admin, "usuario.crear", f"{usuario.nombre} <{email}>", f"Rol: {roles_srv.nombre_rol(db, datos.rol)}")
    db.commit()
    enviar_restablecer(usuario, tareas, nueva_cuenta=True)
    return _usuario_admin(db, usuario)


def _validar_rol(db: Session, quien: Usuario, clave: str) -> RolUsuario:
    rol = db.get(RolUsuario, clave)
    if rol is None:
        raise HTTPException(status_code=422, detail="Ese rol no existe")
    if clave == Rol.ADMIN and quien.rol != Rol.ADMIN:
        raise HTTPException(status_code=403, detail="Solo un Administrador puede dar el rol de Administrador")
    return rol


def _admins_activos(db: Session) -> int:
    return db.scalar(select(func.count(Usuario.id)).where(Usuario.rol == Rol.ADMIN.value, Usuario.activo.is_(True))) or 0


@r_usuarios.patch("/usuarios/{usuario_id}", response_model=UsuarioAdmin)
def actualizar_usuario(usuario_id: uuid.UUID, datos: CambiosUsuario, admin: Admin, db: DbSession, tareas: BackgroundTasks):
    usuario = _obtener_usuario(db, usuario_id)
    cambios = datos.model_dump(exclude_unset=True)
    if usuario.id == admin.id and (("rol" in cambios and cambios["rol"] != usuario.rol) or cambios.get("activo") is False):
        raise HTTPException(status_code=409, detail="No puedes cambiar tu propio rol ni desactivar tu propia cuenta")
    if usuario.rol == Rol.ADMIN and admin.rol != Rol.ADMIN and cambios:
        raise HTTPException(status_code=403, detail="Solo un Administrador puede modificar a otro Administrador")
    if cambios.get("rol"):
        _validar_rol(db, admin, cambios["rol"])
    if "rol" in cambios and cambios["rol"] is not None and not ajustes_srv.dominio_permitido(db, usuario.email, cambios["rol"]):
        raise HTTPException(status_code=409, detail=(
            f"{usuario.email} no es un correo institucional: esta cuenta solo puede ser de aliado externo. "
            + ajustes_srv.mensaje_dominio(db)))
    deja_de_ser_admin = usuario.rol == Rol.ADMIN and usuario.activo and (
        ("rol" in cambios and cambios["rol"] != Rol.ADMIN) or cambios.get("activo") is False)
    if deja_de_ser_admin and _admins_activos(db) <= 1:
        raise HTTPException(status_code=409, detail="Debe quedar al menos un administrador activo")

    avisos: list[str] = []
    detalle: list[str] = []
    for campo, valor in cambios.items():
        anterior = getattr(usuario, campo)
        if valor is None and campo != "programa" or valor == anterior:
            continue
        setattr(usuario, campo, valor)
        if campo == "rol":
            nuevo = roles_srv.nombre_rol(db, valor)
            detalle.append(f"rol: {roles_srv.nombre_rol(db, anterior)} → {nuevo}")
            avisos.append(f"Tu rol ahora es {nuevo}.")
        elif campo == "activo":
            detalle.append("cuenta activada" if valor else "cuenta desactivada")
            avisos.append("Tu cuenta fue reactivada: ya puedes ingresar." if valor
                          else "Tu cuenta fue desactivada. Si crees que es un error, escribe al equipo de Proyecta.")
        elif campo == "verificado":
            detalle.append("correo marcado como verificado" if valor else "correo marcado sin verificar")
        else:
            detalle.append(f"{campo}: «{anterior or ''}» → «{valor or ''}»")
    if detalle:
        registrar(db, admin, "usuario.editar", f"{usuario.nombre} <{usuario.email}>", "; ".join(detalle))
    if "rol" in cambios or "programa" in cambios:
        from app.modules.insignias.servicio import evaluar
        db.flush()
        evaluar(db, usuario, tareas)  # insignias que dependen del rol o del programa
    if avisos:
        notificar(db, usuario, TipoNotificacion.CUENTA, "Un administrador actualizó tu cuenta", " ".join(avisos),
                  "/perfil", tareas, parrafos=avisos, boton="Ir a Proyecta")
    db.commit()
    return _usuario_admin(db, usuario)


@r_usuarios.post("/usuarios/{usuario_id}/restablecer", status_code=status.HTTP_202_ACCEPTED)
def enviar_enlace_contrasena(usuario_id: uuid.UUID, admin: Admin, db: DbSession, tareas: BackgroundTasks):
    usuario = _obtener_usuario(db, usuario_id)
    if not usuario.activo:
        raise HTTPException(status_code=409, detail="La cuenta está desactivada")
    enviar_restablecer(usuario, tareas)
    registrar(db, admin, "usuario.restablecer", f"{usuario.nombre} <{usuario.email}>", "Enlace para cambiar la contraseña")
    db.commit()
    return {"detalle": f"Enviamos a {usuario.email} un enlace para elegir una contraseña nueva."}


# ---- Catálogos: áreas y ODS ------------------------------------------------------------------

def _area_admin(db: Session, a: Area) -> AreaAdmin:
    return AreaAdmin(
        id=a.id, nombre=a.nombre,
        proyectos=db.scalar(select(func.count(Proyecto.id)).where(Proyecto.area_id == a.id)) or 0,
        oportunidades=db.scalar(select(func.count()).where(oportunidad_areas.c.area_id == a.id)) or 0,
    )


def _nombre_area_libre(db: Session, nombre: str, excepto: int | None = None) -> str:
    nombre = nombre.strip()
    existe = db.scalar(select(Area.id).where(func.lower(Area.nombre) == nombre.lower()))
    if existe and existe != excepto:
        raise HTTPException(status_code=409, detail=f"Ya existe el área «{nombre}»")
    return nombre


@r_catalogos.get("/areas", response_model=list[AreaAdmin])
def listar_areas(db: DbSession):
    return [_area_admin(db, a) for a in db.scalars(select(Area).order_by(Area.nombre))]


@r_catalogos.post("/areas", response_model=AreaAdmin, status_code=status.HTTP_201_CREATED)
def crear_area(datos: AreaEntrada, admin: Admin, db: DbSession):
    area = Area(nombre=_nombre_area_libre(db, datos.nombre))
    db.add(area)
    registrar(db, admin, "area.crear", area.nombre)
    db.commit()
    return _area_admin(db, area)


@r_catalogos.put("/areas/{area_id}", response_model=AreaAdmin)
def renombrar_area(area_id: int, datos: AreaEntrada, admin: Admin, db: DbSession):
    area = db.get(Area, area_id)
    if area is None:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    anterior, area.nombre = area.nombre, _nombre_area_libre(db, datos.nombre, area.id)
    registrar(db, admin, "area.editar", area.nombre, f"Antes: {anterior}")
    db.commit()
    return _area_admin(db, area)


@r_catalogos.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_area(area_id: int, admin: Admin, db: DbSession):
    area = db.get(Area, area_id)
    if area is None:
        raise HTTPException(status_code=404, detail="Área no encontrada")
    uso = _area_admin(db, area)
    if uso.proyectos or uso.oportunidades:
        raise HTTPException(status_code=409, detail=(
            f"No se puede eliminar: la usan {uso.proyectos} proyectos y {uso.oportunidades} oportunidades. "
            "Cámbiales el área primero o renómbrala."))
    registrar(db, admin, "area.eliminar", area.nombre)
    db.delete(area)
    db.commit()


@r_catalogos.get("/ods", response_model=list[OdsAdmin])
def listar_ods(db: DbSession):
    return db.scalars(select(Ods).order_by(Ods.id)).all()


@r_catalogos.put("/ods/{ods_id}", response_model=OdsAdmin)
def renombrar_ods(ods_id: int, datos: OdsEntrada, admin: Admin, db: DbSession):
    ods = db.get(Ods, ods_id)
    if ods is None:
        raise HTTPException(status_code=404, detail="ODS no encontrado")
    anterior, ods.nombre = ods.nombre, datos.nombre.strip()
    registrar(db, admin, "ods.editar", f"ODS {ods.id}: {ods.nombre}", f"Antes: {anterior}")
    db.commit()
    return ods


# ---- Catálogos de colaboración: motivos, tipos de aporte y plantillas -------------------------

def _crud(router: APIRouter, ruta: str, modelo, entrada, salida, etiqueta: str, orden):
    """Registra listar/crear/editar/eliminar para un catálogo simple."""

    def _obtener(db: Session, item_id: int):
        item = db.get(modelo, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"{etiqueta.capitalize()} no encontrado")
        return item

    def _nombre(item) -> str:
        return getattr(item, "nombre", None) or getattr(item, "titulo", "")

    @router.get(f"/{ruta}", response_model=list[salida], name=f"listar_{ruta}")
    def listar(db: DbSession):
        return db.scalars(select(modelo).order_by(*orden)).all()

    @router.post(f"/{ruta}", response_model=salida, status_code=status.HTTP_201_CREATED, name=f"crear_{ruta}")
    def crear(datos: entrada, admin: Admin, db: DbSession):
        item = modelo(**datos.model_dump())
        db.add(item)
        db.flush()
        registrar(db, admin, f"{ruta}.crear", _nombre(item))
        db.commit()
        return item

    @router.put(f"/{ruta}/{{item_id}}", response_model=salida, name=f"editar_{ruta}")
    def editar(item_id: int, datos: entrada, admin: Admin, db: DbSession):
        item = _obtener(db, item_id)
        for campo, valor in datos.model_dump().items():
            setattr(item, campo, valor)
        registrar(db, admin, f"{ruta}.editar", _nombre(item), "activo" if item.activo else "inactivo")
        db.commit()
        return item

    @router.delete(f"/{ruta}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT, name=f"eliminar_{ruta}")
    def eliminar(item_id: int, admin: Admin, db: DbSession):
        item = _obtener(db, item_id)
        registrar(db, admin, f"{ruta}.eliminar", _nombre(item))
        db.delete(item)
        db.commit()


def _unico_tipo_aporte(db: Session, nombre: str, excepto: int | None) -> None:
    existe = db.scalar(select(TipoAporte.id).where(func.lower(TipoAporte.nombre) == nombre.strip().lower()))
    if existe and existe != excepto:
        raise HTTPException(status_code=409, detail=f"Ya existe el tipo de aporte «{nombre}»")


_crud(r_colaboracion, "motivos", Motivo, MotivoEntrada, MotivoSalida, "motivo", (Motivo.tipo, Motivo.orden, Motivo.id))
_crud(r_colaboracion, "plantillas", Plantilla, PlantillaEntrada, PlantillaSalida, "plantilla", (Plantilla.orden, Plantilla.id))


# Los tipos de aporte tienen nombre único: se validan aparte.
@r_colaboracion.get("/tipos-aporte", response_model=list[TipoAporteSalida])
def listar_tipos_aporte(db: DbSession):
    return db.scalars(select(TipoAporte).order_by(TipoAporte.orden, TipoAporte.nombre)).all()


@r_colaboracion.post("/tipos-aporte", response_model=TipoAporteSalida, status_code=status.HTTP_201_CREATED)
def crear_tipo_aporte(datos: TipoAporteEntrada, admin: Admin, db: DbSession):
    _unico_tipo_aporte(db, datos.nombre, None)
    item = TipoAporte(**{**datos.model_dump(), "nombre": datos.nombre.strip()})
    db.add(item)
    registrar(db, admin, "tipos-aporte.crear", item.nombre)
    db.commit()
    return item


@r_colaboracion.put("/tipos-aporte/{item_id}", response_model=TipoAporteSalida)
def editar_tipo_aporte(item_id: int, datos: TipoAporteEntrada, admin: Admin, db: DbSession):
    item = db.get(TipoAporte, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Tipo de aporte no encontrado")
    _unico_tipo_aporte(db, datos.nombre, item.id)
    for campo, valor in datos.model_dump().items():
        setattr(item, campo, valor.strip() if campo == "nombre" else valor)
    registrar(db, admin, "tipos-aporte.editar", item.nombre, "activo" if item.activo else "inactivo")
    db.commit()
    return item


@r_colaboracion.delete("/tipos-aporte/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tipo_aporte(item_id: int, admin: Admin, db: DbSession):
    item = db.get(TipoAporte, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Tipo de aporte no encontrado")
    registrar(db, admin, "tipos-aporte.eliminar", item.nombre)
    db.delete(item)  # las solicitudes conservan el nombre en `rol_propuesto`
    db.commit()


# ---- Ajustes generales -----------------------------------------------------------------------

@r_ajustes.get("/ajustes", response_model=ajustes_srv.Ajustes)
def leer_ajustes(db: DbSession):
    return ajustes_srv.leer(db)


@r_ajustes.put("/ajustes", response_model=ajustes_srv.Ajustes)
def guardar_ajustes(datos: ajustes_srv.Ajustes, admin: Admin, db: DbSession):
    antes = ajustes_srv.leer(db).model_dump()
    cambios = [f"{k}: {antes[k]} → {v}" for k, v in datos.model_dump().items() if antes.get(k) != v]
    if cambios:
        registrar(db, admin, "ajustes.editar", "Ajustes generales", "; ".join(cambios))
    return ajustes_srv.guardar(db, datos)


@r_ajustes.post("/resumenes", response_model=ResultadoResumen)
def enviar_resumenes_ahora(admin: Admin, db: DbSession):
    """Envía ya el resumen de mensajes sin leer (normalmente sale solo cada pocos minutos)."""
    avisos = enviar_resumenes(db)
    registrar(db, admin, "resumenes.enviar", "Resumen de mensajes sin leer", f"{avisos} avisos")
    db.commit()
    return ResultadoResumen(avisos=avisos)


# ---- Moderación ------------------------------------------------------------------------------

@r_moderacion.get("/proyectos", response_model=list[ProyectoAdmin])
def listar_proyectos(db: DbSession, q: str | None = None, limite: int = Query(default=100, ge=1, le=500)):
    stmt = select(Proyecto)
    if q:
        patron = f"%{q.strip()}%"
        stmt = stmt.outerjoin(Usuario, Usuario.id == Proyecto.creado_por_id).where(
            or_(Proyecto.titulo.ilike(patron), Proyecto.lider.ilike(patron), Usuario.nombre.ilike(patron), Usuario.email.ilike(patron)))
    salida = []
    for p in db.scalars(stmt.order_by(Proyecto.creado_en.desc(), Proyecto.titulo).limit(limite)).unique():
        dueno = db.get(Usuario, p.creado_por_id) if p.creado_por_id else None
        salida.append(ProyectoAdmin(
            id=p.id, titulo=p.titulo, area=p.area.nombre, estado=p.estado.value,
            responsable_id=dueno.id if dueno else None, responsable_nombre=dueno.nombre if dueno else None,
            responsable_email=dueno.email if dueno else None,
            miembros=db.scalar(select(func.count()).where(Miembro.proyecto_id == p.id)) or 0,
            solicitudes_pendientes=db.scalar(select(func.count()).where(
                Solicitud.proyecto_id == p.id, Solicitud.estado == EstadoSolicitud.PENDIENTE)) or 0,
            creado_en=p.creado_en,
        ))
    return salida


@r_moderacion.delete("/proyectos/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proyecto(proyecto_id: uuid.UUID, datos: Eliminacion, admin: Admin, db: DbSession, tareas: BackgroundTasks):
    """Quita un proyecto y le explica el motivo a quien lo registró."""
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    dueno = db.get(Usuario, proyecto.creado_por_id) if proyecto.creado_por_id else None
    if dueno is not None and dueno.id != admin.id:
        notificar(db, dueno, TipoNotificacion.MODERACION, f"Se retiró tu proyecto «{proyecto.titulo}»",
                  f"Motivo: {datos.motivo.strip()}", "/perfil", tareas,
                  parrafos=["Un administrador retiró tu proyecto de Proyecta."],
                  detalles=[("Proyecto", proyecto.titulo), ("Motivo", datos.motivo.strip())], boton="Ir a mi perfil")
    registrar(db, admin, "proyecto.eliminar", proyecto.titulo, f"Motivo: {datos.motivo.strip()}")
    db.delete(proyecto)
    db.commit()


# ---- Bitácora --------------------------------------------------------------------------------

@r_bitacora.get("/registro", response_model=list[RegistroSalida])
def bitacora(db: DbSession, limite: int = Query(default=100, ge=1, le=500), accion: str | None = None):
    stmt = select(RegistroAdmin)
    if accion:
        stmt = stmt.where(RegistroAdmin.accion.startswith(accion))
    return [
        RegistroSalida(id=r.id, admin_nombre=r.admin.nombre if r.admin else "Admin eliminado", accion=r.accion,
                       objeto=r.objeto, detalle=r.detalle, creado_en=r.creado_en)
        for r in db.scalars(stmt.order_by(RegistroAdmin.creado_en.desc()).limit(limite))
    ]
