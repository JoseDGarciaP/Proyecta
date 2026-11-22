import uuid
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.deps import Admin, DbSession, requiere
from app.modules.admin.bitacora import registrar
from app.modules.catalogo.models import Area, Ods
from app.modules.catalogo.service import areas_por_nombre, ods_por_id
from app.modules.oportunidades.models import Oportunidad, TipoOportunidad
from app.modules.oportunidades.schemas import OportunidadEntrada, OportunidadSalida

router = APIRouter(prefix="/api/oportunidades", tags=["oportunidades"])


def _obtener(db: Session, oportunidad_id: uuid.UUID) -> Oportunidad:
    oportunidad = db.get(Oportunidad, oportunidad_id)
    if oportunidad is None:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return oportunidad


def _aplicar(db: Session, oportunidad: Oportunidad, datos: OportunidadEntrada) -> None:
    for campo, valor in datos.model_dump(exclude={"areas", "ods"}).items():
        setattr(oportunidad, campo, valor)
    oportunidad.areas = areas_por_nombre(db, datos.areas)
    oportunidad.ods = ods_por_id(db, datos.ods)


@router.get("", response_model=list[OportunidadSalida], dependencies=[Depends(requiere("oportunidades.ver"))])
def listar_oportunidades(
    db: DbSession,
    q: str | None = None,
    area: str | None = None,
    ods: int | None = None,
    tipo: TipoOportunidad | None = None,
    abiertas: bool = Query(default=False, description="Solo las que no han cerrado"),
    archivadas: bool = Query(default=False, description="Ver las archivadas en lugar de las vigentes"),
):
    stmt = select(Oportunidad).where(Oportunidad.archivada.is_(archivadas))
    if q:
        patron = f"%{q}%"
        stmt = stmt.where(or_(Oportunidad.titulo.ilike(patron), Oportunidad.entidad.ilike(patron),
                              Oportunidad.descripcion.ilike(patron)))
    if area:
        stmt = stmt.where(Oportunidad.areas.any(Area.nombre == area))
    if ods:
        stmt = stmt.where(Oportunidad.ods.any(Ods.id == ods))
    if tipo:
        stmt = stmt.where(Oportunidad.tipo == tipo)
    if abiertas:
        stmt = stmt.where(Oportunidad.cierra_en >= date.today())
    return [OportunidadSalida.de(o) for o in db.scalars(stmt.order_by(Oportunidad.cierra_en))]


@router.get("/{oportunidad_id}", response_model=OportunidadSalida, dependencies=[Depends(requiere("oportunidades.ver"))])
def leer_oportunidad(oportunidad_id: uuid.UUID, db: DbSession):
    return OportunidadSalida.de(_obtener(db, oportunidad_id))


@router.post("", response_model=OportunidadSalida, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere("oportunidades.gestionar"))])
def crear_oportunidad(datos: OportunidadEntrada, admin: Admin, db: DbSession):
    oportunidad = Oportunidad(creado_por_id=admin.id)
    _aplicar(db, oportunidad, datos)
    db.add(oportunidad)
    registrar(db, admin, "oportunidad.crear", oportunidad.titulo)
    db.commit()
    return OportunidadSalida.de(oportunidad)


@router.put("/{oportunidad_id}", response_model=OportunidadSalida, dependencies=[Depends(requiere("oportunidades.gestionar"))])
def actualizar_oportunidad(oportunidad_id: uuid.UUID, datos: OportunidadEntrada, admin: Admin, db: DbSession,
                           tareas: BackgroundTasks):
    oportunidad = _obtener(db, oportunidad_id)
    fechas_antes = (oportunidad.abre_en, oportunidad.cierra_en)
    _aplicar(db, oportunidad, datos)
    if (oportunidad.abre_en, oportunidad.cierra_en) != fechas_antes:
        # Ep6-Hu5: si cambian las fechas se avisa a los equipos que ya postularon.
        if oportunidad.cierra_en != fechas_antes[1]:
            oportunidad.aviso_7_dias = oportunidad.aviso_1_dia = False
        _avisar_postulantes(db, oportunidad, f"Cambiaron las fechas de «{oportunidad.titulo}»",
                            f"Ahora abre el {oportunidad.abre_en.isoformat()} y cierra el {oportunidad.cierra_en.isoformat()}.",
                            tareas, [("Antes", f"{fechas_antes[0].isoformat()} a {fechas_antes[1].isoformat()}"),
                                     ("Ahora", f"{oportunidad.abre_en.isoformat()} a {oportunidad.cierra_en.isoformat()}")])
    registrar(db, admin, "oportunidad.editar", oportunidad.titulo)
    db.commit()
    return OportunidadSalida.de(oportunidad)


class Motivo(BaseModel):
    motivo: str = Field(default="", max_length=1000)


def _avisar_postulantes(db: Session, oportunidad: Oportunidad, titulo: str, cuerpo: str, tareas: BackgroundTasks,
                        detalles: list[tuple[str, str]]) -> int:
    from app.modules.notificaciones.models import TipoNotificacion
    from app.modules.notificaciones.servicio import notificar
    from app.modules.postulaciones.models import EstadoPostulacion, Postulacion
    from app.modules.postulaciones.router import _equipo
    from app.modules.usuarios.models import Usuario

    personas: set[uuid.UUID] = set()
    for p in db.scalars(select(Postulacion).where(Postulacion.oportunidad_id == oportunidad.id,
                                                  Postulacion.estado != EstadoPostulacion.RETIRADA)).unique():
        personas.update(_equipo(db, p.proyecto))
    for uid in personas:
        if (u := db.get(Usuario, uid)) is not None:
            notificar(db, u, TipoNotificacion.CONVOCATORIA, titulo, cuerpo, "/oportunidades", tareas, detalles=detalles)
    return len(personas)


@router.delete("/{oportunidad_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere("oportunidades.gestionar"))])
def eliminar_oportunidad(oportunidad_id: uuid.UUID, admin: Admin, db: DbSession, tareas: BackgroundTasks,
                         datos: Motivo | None = Body(default=None)):
    """Borra la oportunidad; si ya tiene postulaciones se archiva y se avisa a esos equipos (Ep6-Hu5)."""
    from app.modules.postulaciones.models import Postulacion

    oportunidad = _obtener(db, oportunidad_id)
    motivo = (datos.motivo.strip() if datos else "") or "Sin motivo indicado"
    if db.scalar(select(Postulacion.id).where(Postulacion.oportunidad_id == oportunidad.id).limit(1)):
        oportunidad.archivada = True
        _avisar_postulantes(db, oportunidad, f"Se archivó la convocatoria «{oportunidad.titulo}»", f"Motivo: {motivo}",
                            tareas, [("Motivo", motivo)])
        registrar(db, admin, "oportunidad.archivar", oportunidad.titulo, f"Motivo: {motivo}")
    else:
        registrar(db, admin, "oportunidad.eliminar", oportunidad.titulo, f"Motivo: {motivo}")
        db.delete(oportunidad)
    db.commit()


@router.post("/{oportunidad_id}/restaurar", response_model=OportunidadSalida, dependencies=[Depends(requiere("oportunidades.gestionar"))])
def restaurar_oportunidad(oportunidad_id: uuid.UUID, admin: Admin, db: DbSession):
    oportunidad = _obtener(db, oportunidad_id)
    oportunidad.archivada = False
    registrar(db, admin, "oportunidad.restaurar", oportunidad.titulo)
    db.commit()
    return OportunidadSalida.de(oportunidad)
