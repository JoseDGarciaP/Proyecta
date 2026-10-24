import uuid
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.core.deps import Admin, DbSession, UsuarioActual, get_current_user, requiere
from app.modules.admin.bitacora import registrar
from app.modules.experiencia import servicio
from app.modules.experiencia.models import AccionXP, MovimientoXP, Nivel
from app.modules.experiencia.schemas import (
    AccionEntrada, AccionSalida, Ajuste, ExperienciaBreve, MiExperiencia, MovimientoSalida, NivelBreve, NivelEntrada,
    NivelSalida, PersonaXP, PuestoXP, ResumenUsuarioXP, Siguiente,
)
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/experiencia", tags=["experiencia"], dependencies=[Depends(get_current_user)])
admin = APIRouter(prefix="/api/admin/experiencia", tags=["administración"], dependencies=[Depends(requiere("admin.experiencia"))])

NOMBRES_ESPECIALES = {"ajuste": "Ajuste de la administración", "evidencia": "Certificado o evidencia aprobada"}


def _breve(nivel: Nivel | None, niveles: list[Nivel]) -> NivelBreve | None:
    if nivel is None:
        return None
    posicion = next((k for k, n in enumerate(niveles, start=1) if n.id == nivel.id), 0)
    return NivelBreve(id=nivel.id, nombre=nivel.nombre, icono=nivel.icono, color=nivel.color, posicion=posicion)


def _nivel_salida(db: Session, n: Nivel, niveles: list[Nivel]) -> NivelSalida:
    s = NivelSalida.model_validate(n)
    s.posicion = next((k for k, x in enumerate(niveles, start=1) if x.id == n.id), 0)
    s.personas = db.scalar(select(func.count(Usuario.id)).where(Usuario.nivel_id == n.id, Usuario.activo.is_(True))) or 0
    return s


def _movimientos(db: Session, usuario_id, limite: int = 50) -> list[MovimientoSalida]:
    acciones = {a.clave: a.nombre for a in db.scalars(select(AccionXP))}
    filas = db.scalars(select(MovimientoXP).where(MovimientoXP.usuario_id == usuario_id)
                       .order_by(MovimientoXP.creado_en.desc()).limit(limite)).unique()
    return [MovimientoSalida(id=m.id, accion=m.accion, accion_nombre=acciones.get(m.accion) or NOMBRES_ESPECIALES.get(m.accion, m.accion),
                             puntos=m.puntos, detalle=m.detalle, otorgado_por=m.otorgado_por.nombre if m.otorgado_por else None,
                             creado_en=m.creado_en) for m in filas]


@router.get("/mia", response_model=MiExperiencia)
def mi_experiencia(usuario: UsuarioActual, db: DbSession):
    from app.modules.insignias.models import Insignia

    niveles = servicio.niveles_ordenados(db)
    est = servicio.estado(db, usuario, niveles)
    siguiente = None
    if est.siguiente:
        n = est.siguiente
        faltan = [i for i in (n.insignias_requeridas or []) if i not in est.insignias]
        nombres = [i.nombre for i in db.scalars(select(Insignia).where(Insignia.id.in_(faltan)))] if faltan else []
        siguiente = Siguiente(nivel=_nivel_salida(db, n, niveles), xp_faltante=max(0, n.xp_minima - (usuario.xp or 0)),
                              insignias_faltantes=max(0, n.insignias_minimas - len(est.insignias)), requeridas_faltantes=nombres)
    semana = db.scalar(select(func.coalesce(func.sum(MovimientoXP.puntos), 0)).where(
        MovimientoXP.usuario_id == usuario.id, MovimientoXP.creado_en >= utcnow() - timedelta(days=7))) or 0
    return MiExperiencia(
        xp=usuario.xp or 0, xp_semana=semana, nivel=_breve(est.actual, niveles), siguiente=siguiente,
        total_niveles=len(niveles), historial=_movimientos(db, usuario.id),
        acciones=db.scalars(select(AccionXP).where(AccionXP.activo.is_(True), AccionXP.puntos > 0).order_by(AccionXP.orden)).all(),
    )


@router.get("/niveles", response_model=list[NivelSalida])
def niveles(db: DbSession):
    ordenados = servicio.niveles_ordenados(db)
    return [_nivel_salida(db, n, ordenados) for n in ordenados]


@router.get("/acciones", response_model=list[AccionSalida])
def acciones(db: DbSession):
    return db.scalars(select(AccionXP).where(AccionXP.activo.is_(True), AccionXP.puntos > 0).order_by(AccionXP.orden)).all()


@router.get("/de", response_model=dict[str, ExperienciaBreve])
def experiencia_de(db: DbSession, ids: str = Query(description="ids de usuario separados por coma (máx. 100)")):
    """Nivel junto al nombre en fichas, miembros, sugerencias y ranking."""
    lista = []
    for x in ids.split(",")[:100]:
        try:
            lista.append(uuid.UUID(x.strip()))
        except ValueError:
            continue
    niveles = servicio.niveles_ordenados(db)
    por_id = {n.id: n for n in niveles}
    usuarios = db.scalars(select(Usuario).where(Usuario.id.in_(lista))).unique().all() if lista else []
    return {str(u.id): ExperienciaBreve(xp=u.xp or 0, nivel=_breve(por_id.get(u.nivel_id), niveles)) for u in usuarios}


@router.get("/ranking", response_model=list[PuestoXP], dependencies=[Depends(requiere("usuarios.ver"))])
def ranking(db: DbSession, periodo: Literal["semana", "mes", "siempre"] = "siempre", limite: int = Query(default=25, ge=1, le=100)):
    niveles = servicio.niveles_ordenados(db)
    por_id = {n.id: n for n in niveles}
    if periodo == "siempre":
        filas = [(u, u.xp or 0) for u in db.scalars(select(Usuario).where(Usuario.activo.is_(True), Usuario.xp > 0)
                                                      .order_by(Usuario.xp.desc(), Usuario.nombre).limit(limite)).unique()]
    else:
        desde = utcnow() - timedelta(days=7 if periodo == "semana" else 30)
        suma = func.sum(MovimientoXP.puntos).label("suma")
        filas = db.execute(select(Usuario, suma).join(MovimientoXP, MovimientoXP.usuario_id == Usuario.id)
                           .where(Usuario.activo.is_(True), MovimientoXP.creado_en >= desde)
                           .group_by(Usuario.id).having(suma > 0).order_by(suma.desc()).limit(limite)).unique().all()
    salida, posicion, anterior = [], 0, None
    for k, (u, xp) in enumerate(filas, start=1):
        if xp != anterior:
            posicion, anterior = k, xp
        salida.append(PuestoXP(posicion=posicion, usuario_id=u.id, nombre=u.nombre, rol_nombre=u.rol_nombre, programa=u.programa,
                               xp=xp, xp_total=u.xp or 0, nivel=_breve(por_id.get(u.nivel_id), niveles)))
    return salida


# ---- Administración --------------------------------------------------------------------------

@admin.get("/acciones", response_model=list[AccionSalida])
def acciones_admin(db: DbSession):
    return db.scalars(select(AccionXP).order_by(AccionXP.orden)).all()


@admin.put("/acciones/{clave}", response_model=AccionSalida)
def editar_accion(clave: str, datos: AccionEntrada, yo: Admin, db: DbSession):
    accion = db.get(AccionXP, clave)
    if accion is None:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    antes = f"{accion.puntos} XP, tope {accion.tope_diario or '—'}"
    for campo, valor in datos.model_dump().items():
        setattr(accion, campo, valor)
    registrar(db, yo, "experiencia.accion", accion.nombre, f"{antes} → {accion.puntos} XP, tope {accion.tope_diario or '—'}"
              + ("" if accion.activo else " (inactiva)"))
    db.commit()
    return accion


def _validar_nivel(db: Session, datos: NivelEntrada, excepto: int | None = None) -> dict:
    from app.modules.insignias.models import Insignia
    from app.modules.insignias.servicio import COLORES, ICONOS

    if datos.icono not in ICONOS:
        raise HTTPException(status_code=422, detail="Ícono no válido")
    if datos.color not in COLORES:
        raise HTTPException(status_code=422, detail="Color no válido")
    existe = db.scalar(select(Nivel.id).where(func.lower(Nivel.nombre) == datos.nombre.strip().lower()))
    if existe and existe != excepto:
        raise HTTPException(status_code=409, detail=f"Ya existe el nivel «{datos.nombre}»")
    requeridas = list(dict.fromkeys(datos.insignias_requeridas))
    if requeridas and len(db.scalars(select(Insignia.id).where(Insignia.id.in_(requeridas))).all()) != len(requeridas):
        raise HTTPException(status_code=422, detail="Alguna insignia obligatoria no existe")
    return {**datos.model_dump(), "nombre": datos.nombre.strip(), "insignias_requeridas": requeridas}


@admin.post("/niveles", response_model=NivelSalida, status_code=status.HTTP_201_CREATED)
def crear_nivel(datos: NivelEntrada, yo: Admin, db: DbSession):
    nivel = Nivel(**_validar_nivel(db, datos))
    db.add(nivel)
    registrar(db, yo, "experiencia.nivel", nivel.nombre, f"Nuevo: {nivel.xp_minima} XP, {nivel.insignias_minimas} insignias")
    db.commit()
    servicio.recalcular_todos(db)
    return _nivel_salida(db, nivel, servicio.niveles_ordenados(db))


@admin.put("/niveles/{nivel_id}", response_model=NivelSalida)
def editar_nivel(nivel_id: int, datos: NivelEntrada, yo: Admin, db: DbSession):
    nivel = db.get(Nivel, nivel_id)
    if nivel is None:
        raise HTTPException(status_code=404, detail="Nivel no encontrado")
    for campo, valor in _validar_nivel(db, datos, nivel.id).items():
        setattr(nivel, campo, valor)
    registrar(db, yo, "experiencia.nivel", nivel.nombre, f"{nivel.xp_minima} XP, {nivel.insignias_minimas} insignias")
    db.commit()
    servicio.recalcular_todos(db)
    return _nivel_salida(db, nivel, servicio.niveles_ordenados(db))


@admin.delete("/niveles/{nivel_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_nivel(nivel_id: int, yo: Admin, db: DbSession):
    nivel = db.get(Nivel, nivel_id)
    if nivel is None:
        raise HTTPException(status_code=404, detail="Nivel no encontrado")
    if db.scalar(select(func.count(Nivel.id))) <= 1:
        raise HTTPException(status_code=409, detail="Debe quedar al menos un nivel")
    registrar(db, yo, "experiencia.nivel", nivel.nombre, "Eliminado")
    db.execute(update(Usuario).where(Usuario.nivel_id == nivel.id).values(nivel_id=None))
    db.delete(nivel)
    db.commit()
    servicio.recalcular_todos(db)


@admin.post("/ajustes", response_model=ResumenUsuarioXP)
def ajustar(datos: Ajuste, yo: Admin, db: DbSession, tareas: BackgroundTasks):
    """Sumar o quitar experiencia a mano (p. ej. por asistir a un evento), con motivo."""
    usuario = db.get(Usuario, datos.usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    servicio.sumar(db, usuario, "ajuste", None, datos.motivo.strip(), tareas, puntos=datos.puntos, por=yo)
    registrar(db, yo, "experiencia.ajuste", usuario.nombre, f"{datos.puntos:+d} XP · {datos.motivo.strip()}")
    if datos.puntos > 0:
        from app.modules.notificaciones.models import TipoNotificacion
        from app.modules.notificaciones.servicio import notificar
        notificar(db, usuario, TipoNotificacion.NIVEL, f"Recibiste {datos.puntos} puntos de experiencia", datos.motivo.strip(),
                  "/perfil#nivel", tareas, boton="Ver mi experiencia")
    db.commit()
    return resumen_usuario(usuario.id, db)


@admin.get("/personas", response_model=list[PersonaXP])
def buscar_personas(db: DbSession, q: str = Query(min_length=2, max_length=100)):
    """Buscar a quién ajustarle la experiencia (sin necesitar el permiso de gestionar usuarios)."""
    patron = f"%{q.strip()}%"
    niveles = servicio.niveles_ordenados(db)
    usuarios = db.scalars(select(Usuario).where(or_(Usuario.nombre.ilike(patron), Usuario.email.ilike(patron)))
                          .order_by(Usuario.nombre).limit(10)).unique().all()
    return [PersonaXP(id=u.id, nombre=u.nombre, email=u.email, rol_nombre=u.rol_nombre, xp=u.xp or 0,
                      nivel=_breve(next((n for n in niveles if n.id == u.nivel_id), None), niveles)) for u in usuarios]


@admin.get("/usuarios/{usuario_id}", response_model=ResumenUsuarioXP)
def resumen_usuario(usuario_id: uuid.UUID, db: DbSession):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    niveles = servicio.niveles_ordenados(db)
    return ResumenUsuarioXP(usuario_id=usuario.id, nombre=usuario.nombre, xp=usuario.xp or 0,
                            nivel=_breve(next((n for n in niveles if n.id == usuario.nivel_id), None), niveles),
                            historial=_movimientos(db, usuario.id, 100))


@admin.post("/recalcular")
def recalcular(yo: Admin, db: DbSession):
    for u in db.scalars(select(Usuario)).unique().all():
        servicio.recalcular_xp(db, u)
    n = servicio.recalcular_todos(db)
    registrar(db, yo, "experiencia.recalcular", "Niveles de todas las personas", f"{n} subieron de nivel")
    db.commit()
    return {"subieron": n}
