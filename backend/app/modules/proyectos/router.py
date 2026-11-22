import csv
import io
import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Response, status
from sqlalchemy import String, cast, or_, select
from sqlalchemy.orm import Session

from app.core.deps import DbSession, UsuarioActual, requiere
from app.modules.actores.models import Actor
from app.modules.catalogo.models import Area, Ods
from app.modules.catalogo.service import area_por_nombre, ods_por_id
from app.modules.proyectos.models import CambioProyecto, Estado, Proyecto
from app.modules.proyectos.schemas import CambioSalida, Eliminar, ProyectoActualizar, ProyectoEntrada, ProyectoSalida
from app.modules.roles.servicio import puede
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/proyectos", tags=["proyectos"])


def obtener_proyecto(db: Session, proyecto_id: uuid.UUID) -> Proyecto:
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return proyecto


def _verificar_dueno(db: Session, proyecto: Proyecto, usuario: Usuario) -> None:
    if proyecto.creado_por_id != usuario.id and not puede(db, usuario, "proyectos.moderar"):
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto puede modificarlo")


def _actores(db: Session, ids: list[uuid.UUID]) -> list[Actor]:
    items = db.scalars(select(Actor).where(Actor.id.in_(ids))).all() if ids else []
    if len(items) != len(set(ids)):
        raise HTTPException(status_code=422, detail="Algún actor no existe")
    return list(items)


def _evaluar_logros(db: Session, proyecto: Proyecto, tareas: BackgroundTasks) -> None:
    from app.modules.alianzas.models import Miembro
    from app.modules.insignias.servicio import evaluar_ids

    miembros = db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id)).all()
    evaluar_ids(db, [proyecto.creado_por_id, *miembros], tareas)


def _experiencia(db: Session, proyecto: Proyecto, avance_antes: int, estado_antes, tareas: BackgroundTasks) -> None:
    """XP para el equipo cuando el avance cruza otra decena (10 %, 20 %…) y cuando el proyecto finaliza."""
    from app.modules.alianzas.models import Miembro
    from app.modules.experiencia.servicio import sumar_a_varios

    equipo = [proyecto.creado_por_id, *db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id))]
    for decena in range(avance_antes // 10 + 1, proyecto.avance // 10 + 1):
        sumar_a_varios(db, equipo, "proyecto_avanza", f"{proyecto.id}:{decena * 10}", f"«{proyecto.titulo}» llegó al {decena * 10} %", tareas)
    if proyecto.estado == Estado.FINALIZADO and estado_antes != Estado.FINALIZADO:
        sumar_a_varios(db, equipo, "proyecto_finalizado", str(proyecto.id), f"«{proyecto.titulo}» finalizado", tareas)


def _consulta_proyectos(
    q: str | None = None,
    area: str | None = None,
    estado: Estado | None = None,
    ods: int | None = None,
    programa: str | None = None,
    archivados: bool = False,
):
    stmt = select(Proyecto)
    if not archivados:
        stmt = stmt.where(Proyecto.archivado.is_(False))
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(
            Proyecto.titulo.ilike(patron), Proyecto.resumen.ilike(patron), Proyecto.necesidades.ilike(patron),
            Proyecto.lider.ilike(patron), cast(Proyecto.etiquetas, String).ilike(patron),
        ))
    if programa:
        stmt = stmt.where(Proyecto.creado_por_id.in_(select(Usuario.id).where(Usuario.programa == programa)))
    if area:
        stmt = stmt.where(or_(Proyecto.area.has(Area.nombre == area), Proyecto.areas_extra.any(Area.nombre == area)))
    if estado:
        stmt = stmt.where(Proyecto.estado == estado)
    if ods:
        stmt = stmt.where(Proyecto.ods.any(Ods.id == ods))
    return stmt.order_by(Proyecto.creado_en.desc(), Proyecto.actualizado_en.desc())


@router.get("", response_model=list[ProyectoSalida])
def listar_proyectos(
    db: DbSession,
    q: str | None = Query(default=None, description="Busca en título, resumen, necesidades, líder y etiquetas"),
    area: str | None = None,
    estado: Estado | None = None,
    ods: int | None = None,
    programa: str | None = Query(default=None, description="Programa académico de quien registró el proyecto"),
    limit: int = Query(default=200, le=500),
    offset: int = 0,
):
    orden = _consulta_proyectos(q=q, area=area, estado=estado, ods=ods, programa=programa).limit(limit).offset(offset)
    return [ProyectoSalida.de(p) for p in db.scalars(orden).unique()]


@router.get("/exportar.csv")
def exportar_proyectos_csv(
    db: DbSession,
    q: str | None = Query(default=None, description="Filtra por título, resumen, necesidades, líder y etiquetas"),
    area: str | None = None,
    estado: Estado | None = None,
    ods: int | None = None,
    programa: str | None = None,
):
    """Descarga el listado de proyectos filtrado en formato CSV (con BOM UTF-8 compatible con Excel)."""
    proyectos = list(db.scalars(_consulta_proyectos(q=q, area=area, estado=estado, ods=ods, programa=programa).limit(500)).unique())
    buf = io.StringIO()
    buf.write("\ufeff")  # BOM UTF-8 para que Microsoft Excel reconozca tildes y eñes automáticamente
    writer = csv.writer(buf)
    writer.writerow([
        "ID", "Título", "Área", "Estado", "Avance (%)", "Presupuesto (COP)",
        "Líder", "Integrantes equipo", "ODS", "Actores vinculados",
        "Etiquetas", "Fecha inicio", "Fecha cierre", "Registrado en",
    ])
    for p in proyectos:
        writer.writerow([
            str(p.id),
            p.titulo,
            p.area.nombre,
            p.estado.value,
            p.avance,
            p.presupuesto,
            p.lider,
            ", ".join(p.equipo),
            ", ".join(f"ODS {o.id}" for o in sorted(p.ods, key=lambda x: x.id)),
            ", ".join(a.nombre for a in p.actores),
            ", ".join(p.etiquetas),
            p.fecha_inicio.isoformat(),
            p.fecha_fin.isoformat() if p.fecha_fin else "",
            p.creado_en.isoformat(),
        ])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="proyectos-proyecta.csv"'},
    )


@router.post("", response_model=ProyectoSalida, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requiere("proyectos.crear"))])
def crear_proyecto(datos: ProyectoEntrada, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks):
    proyecto = Proyecto(
        **datos.model_dump(exclude={"area", "areas_extra", "ods", "actores", "lider"}),
        lider=datos.lider.strip() or usuario.nombre,
        creado_por_id=usuario.id,
    )
    proyecto.area = area_por_nombre(db, datos.area)
    proyecto.areas_extra = [area_por_nombre(db, a) for a in dict.fromkeys(datos.areas_extra) if a != datos.area]
    proyecto.ods = ods_por_id(db, datos.ods)
    proyecto.actores = _actores(db, datos.actores)
    db.add(proyecto)
    db.flush()
    from app.modules.experiencia.servicio import sumar
    sumar(db, usuario, "proyecto_registrado", str(proyecto.id), f"Registró «{proyecto.titulo}»", tareas)
    _evaluar_logros(db, proyecto, tareas)
    db.commit()
    return ProyectoSalida.de(proyecto)


@router.get("/{proyecto_id}", response_model=ProyectoSalida)
def leer_proyecto(proyecto_id: uuid.UUID, db: DbSession):
    return ProyectoSalida.de(obtener_proyecto(db, proyecto_id))


@router.patch("/{proyecto_id}", response_model=ProyectoSalida)
def actualizar_proyecto(proyecto_id: uuid.UUID, datos: ProyectoActualizar, usuario: UsuarioActual, db: DbSession,
                        tareas: BackgroundTasks):
    proyecto = obtener_proyecto(db, proyecto_id)
    _verificar_dueno(db, proyecto, usuario)
    cambios = datos.model_dump(exclude_unset=True)
    avance_antes, estado_antes = proyecto.avance, proyecto.estado
    antes = _foto(proyecto)
    if (area := cambios.pop("area", None)) is not None:
        proyecto.area = area_por_nombre(db, area)
    if (extra := cambios.pop("areas_extra", None)) is not None:
        proyecto.areas_extra = [area_por_nombre(db, a) for a in dict.fromkeys(extra) if a != proyecto.area.nombre]
    if (ods := cambios.pop("ods", None)) is not None:
        proyecto.ods = ods_por_id(db, ods)
    if (actores := cambios.pop("actores", None)) is not None:
        proyecto.actores = _actores(db, actores)
    for campo, valor in cambios.items():
        if valor is not None or campo == "fecha_fin":
            setattr(proyecto, campo, valor)
    if proyecto.fecha_fin and proyecto.fecha_fin < proyecto.fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha de cierre no puede ser anterior a la de inicio")
    db.flush()
    _registrar_cambios(db, proyecto, usuario, antes, _foto(proyecto), tareas)
    _experiencia(db, proyecto, avance_antes, estado_antes, tareas)
    _evaluar_logros(db, proyecto, tareas)  # p. ej. «Proyecto cumplido» para todo el equipo
    db.commit()
    return ProyectoSalida.de(proyecto)


@router.delete("/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proyecto(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks,
                      datos: Eliminar | None = Body(default=None)):
    """Borra el proyecto (Ep4-Hu20). Si tiene colaboradores, se archiva y se les avisa en lugar de borrarlo."""
    from app.modules.admin.bitacora import registrar
    from app.modules.alianzas.models import Miembro
    from app.modules.notificaciones.models import TipoNotificacion
    from app.modules.notificaciones.servicio import notificar

    proyecto = obtener_proyecto(db, proyecto_id)
    if proyecto.creado_por_id != usuario.id and not puede(db, usuario, "proyectos.moderar"):
        raise HTTPException(status_code=403, detail="Solo quien registró el proyecto o un administrador puede eliminarlo")
    motivo = (datos.motivo.strip() if datos else "") or "Sin motivo indicado"
    miembros = db.scalars(select(Miembro).where(Miembro.proyecto_id == proyecto.id, Miembro.usuario_id != usuario.id)).all()
    if miembros:
        proyecto.archivado, proyecto.archivado_motivo = True, motivo
        for m in miembros:
            notificar(db, m.usuario, TipoNotificacion.PROYECTO, f"Se archivó el proyecto «{proyecto.titulo}»",
                      f"{usuario.nombre} lo archivó. Motivo: {motivo}", f"/proyectos/{proyecto.id}", tareas,
                      detalles=[("Proyecto", proyecto.titulo), ("Motivo", motivo)])
        registrar(db, usuario, "proyecto.archivar", proyecto.titulo, f"Motivo: {motivo}")
    else:
        registrar(db, usuario, "proyecto.eliminar", proyecto.titulo, f"Motivo: {motivo}")
        db.delete(proyecto)
    db.commit()


@router.get("/{proyecto_id}/cambios", response_model=list[CambioSalida])
def historial_de_cambios(proyecto_id: uuid.UUID, db: DbSession):
    """Quién cambió qué y cuándo (Ep4-Hu18)."""
    obtener_proyecto(db, proyecto_id)
    filas = db.scalars(select(CambioProyecto).where(CambioProyecto.proyecto_id == proyecto_id)
                       .order_by(CambioProyecto.creado_en.desc()).limit(100))
    return [CambioSalida(id=c.id, autor=c.autor.nombre if c.autor else "Usuario eliminado", cambios=c.cambios,
                         creado_en=c.creado_en) for c in filas]


# ---- Historial de cambios -----------------------------------------------------------------------

ETIQUETAS = {
    "titulo": "Título", "resumen": "Resumen", "descripcion": "Descripción", "necesidades": "Necesidades",
    "problema": "Problema", "objetivos": "Objetivos", "area": "Área", "areas_extra": "Áreas adicionales",
    "estado": "Estado", "avance": "Avance", "presupuesto": "Presupuesto", "lider": "Líder", "equipo": "Equipo",
    "etiquetas": "Etiquetas", "fecha_inicio": "Fecha de inicio", "fecha_fin": "Fecha de cierre", "ods": "ODS",
    "actores": "Actores",
}
TEXTOS_LARGOS = {"descripcion", "necesidades", "problema", "objetivos"}


def _foto(p: Proyecto) -> dict[str, str]:
    """Valores legibles de cada campo, para comparar antes y después."""
    return {
        "titulo": p.titulo, "resumen": p.resumen, "descripcion": p.descripcion or "", "necesidades": p.necesidades or "",
        "problema": p.problema or "", "objetivos": p.objetivos or "", "area": p.area.nombre if p.area else "",
        "areas_extra": ", ".join(sorted(a.nombre for a in p.areas_extra)), "estado": p.estado.value if p.estado else "",
        "avance": f"{p.avance} %", "presupuesto": str(p.presupuesto), "lider": p.lider, "equipo": ", ".join(p.equipo or []),
        "etiquetas": ", ".join(p.etiquetas or []), "fecha_inicio": str(p.fecha_inicio or ""), "fecha_fin": str(p.fecha_fin or ""),
        "ods": ", ".join(str(o.id) for o in sorted(p.ods, key=lambda o: o.id)),
        "actores": ", ".join(sorted(a.nombre for a in p.actores)),
    }


def _registrar_cambios(db: Session, proyecto: Proyecto, autor: Usuario, antes: dict, despues: dict,
                       tareas: BackgroundTasks) -> None:
    """Guarda el historial y avisa al equipo qué cambió y quién lo hizo (Ep4-Hu18, Ep6-Hu14)."""
    from app.modules.alianzas.models import Miembro
    from app.modules.notificaciones.models import TipoNotificacion
    from app.modules.notificaciones.servicio import notificar

    cambios = [
        {"campo": ETIQUETAS[c], "antes": "" if c in TEXTOS_LARGOS else antes[c][:120],
         "despues": "(texto actualizado)" if c in TEXTOS_LARGOS else despues[c][:120]}
        for c in ETIQUETAS if antes[c] != despues[c]
    ]
    if not cambios:
        return
    db.add(CambioProyecto(proyecto_id=proyecto.id, autor_id=autor.id, cambios=cambios))
    resumen = "; ".join(f"{c['campo']}: {c['antes']} → {c['despues']}" if c["antes"] else f"{c['campo']} {c['despues']}"
                        for c in cambios[:4])
    destinatarios = {m.usuario_id: m.usuario for m in db.scalars(select(Miembro).where(Miembro.proyecto_id == proyecto.id))}
    if proyecto.creado_por is not None:
        destinatarios[proyecto.creado_por_id] = proyecto.creado_por
    destinatarios.pop(autor.id, None)
    for persona in destinatarios.values():
        notificar(db, persona, TipoNotificacion.PROYECTO, f"{autor.nombre} actualizó «{proyecto.titulo}»", resumen,
                  f"/proyectos/{proyecto.id}", tareas, detalles=[(c["campo"], c["despues"]) for c in cambios[:6]])
