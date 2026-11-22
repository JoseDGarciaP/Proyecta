"""Estadísticas con filtro de fechas y reporte en Excel del panel (Ep4-Hu28, Ep4-Hu29, Ep4-Hu30)."""

from collections import Counter
from datetime import date, datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import excel
from app.core.deps import Admin, DbSession, requiere
from app.modules.admin.bitacora import registrar
from app.modules.alianzas.models import EstadoSolicitud, Solicitud
from app.modules.ia.models import EstadoRecomendacion, RecomendacionGuardada
from app.modules.postulaciones.models import EstadoPostulacion, Postulacion
from app.modules.proyectos.models import Proyecto

router = APIRouter(prefix="/api/admin", tags=["administración"], dependencies=[Depends(requiere("admin.resumen"))])


class Conteo(BaseModel):
    clave: str
    total: int


class Mes(BaseModel):
    mes: str  # AAAA-MM
    proyectos: int
    alianzas: int
    alianzas_aceptadas: int
    postulaciones: int
    postulaciones_aceptadas: int


class EstadisticasDetalle(BaseModel):
    desde: date | None
    hasta: date | None
    proyectos: int
    por_programa: list[Conteo]
    por_area: list[Conteo]
    por_estado: list[Conteo]
    por_mes: list[Mes]
    postulaciones: int
    tasa_exito_postulaciones: float | None  # seleccionadas / decididas
    recomendaciones_generadas: int
    recomendaciones_aceptadas: int
    recomendaciones_anuladas: int
    tasa_aceptacion_recomendaciones: float | None


def _en_rango(d: datetime | date | None, desde: date | None, hasta: date | None) -> bool:
    if d is None:
        return False
    dia = d.date() if isinstance(d, datetime) else d
    return (desde is None or dia >= desde) and (hasta is None or dia <= hasta)


def _mes(d: datetime | date) -> str:
    return d.strftime("%Y-%m")


def _ordenado(c: Counter) -> list[Conteo]:
    return [Conteo(clave=k or "Sin dato", total=n) for k, n in c.most_common()]


def calcular(db: Session, desde: date | None, hasta: date | None) -> tuple[EstadisticasDetalle, list[Proyecto]]:
    proyectos = [p for p in db.scalars(select(Proyecto)).unique() if _en_rango(p.creado_en, desde, hasta)]
    solicitudes = [s for s in db.scalars(select(Solicitud)).unique() if _en_rango(s.creado_en, desde, hasta)]
    postulaciones = [p for p in db.scalars(select(Postulacion)).unique() if _en_rango(p.creado_en, desde, hasta)]
    recs = [r for r in db.scalars(select(RecomendacionGuardada)) if _en_rango(r.creado_en, desde, hasta)]

    meses: dict[str, dict[str, int]] = {}
    def sumar(m: str, campo: str):
        meses.setdefault(m, Counter())[campo] += 1
    for p in proyectos:
        sumar(_mes(p.creado_en), "proyectos")
    for s in solicitudes:
        sumar(_mes(s.creado_en), "alianzas")
        if s.estado in (EstadoSolicitud.ACEPTADA, EstadoSolicitud.ANULADA):
            sumar(_mes(s.creado_en), "alianzas_aceptadas")
    for p in postulaciones:
        sumar(_mes(p.creado_en), "postulaciones")
        if p.estado == EstadoPostulacion.ACEPTADA:
            sumar(_mes(p.creado_en), "postulaciones_aceptadas")

    aceptadas = sum(p.estado == EstadoPostulacion.ACEPTADA for p in postulaciones)
    decididas = aceptadas + sum(p.estado == EstadoPostulacion.NO_SELECCIONADA for p in postulaciones)
    rec_ok = sum(r.estado == EstadoRecomendacion.ACEPTADA for r in recs)
    rec_no = sum(r.estado == EstadoRecomendacion.ANULADA for r in recs)
    datos = EstadisticasDetalle(
        desde=desde, hasta=hasta, proyectos=len(proyectos),
        por_programa=_ordenado(Counter((p.creado_por.programa if p.creado_por else None) or "Sin programa" for p in proyectos)),
        por_area=_ordenado(Counter(p.area.nombre for p in proyectos)),
        por_estado=_ordenado(Counter(p.estado.value for p in proyectos)),
        por_mes=[Mes(mes=m, **{k: v.get(k, 0) for k in ("proyectos", "alianzas", "alianzas_aceptadas", "postulaciones",
                                                         "postulaciones_aceptadas")}) for m, v in sorted(meses.items())],
        postulaciones=len(postulaciones),
        tasa_exito_postulaciones=round(aceptadas / decididas, 3) if decididas else None,
        recomendaciones_generadas=len(recs), recomendaciones_aceptadas=rec_ok, recomendaciones_anuladas=rec_no,
        tasa_aceptacion_recomendaciones=round(rec_ok / len(recs), 3) if recs else None,
    )
    return datos, proyectos


@router.get("/estadisticas/detalle", response_model=EstadisticasDetalle)
def estadisticas_detalle(db: DbSession, desde: date | None = Query(default=None), hasta: date | None = Query(default=None)):
    return calcular(db, desde, hasta)[0]


def _pct(x: float | None) -> str:
    return f"{round(x * 100)} %" if x is not None else "Sin datos"


@router.get("/reporte.xlsx")
def reporte_excel(admin: Admin, db: DbSession, desde: date | None = None, hasta: date | None = None):
    """El panel en Excel, con la fecha de generación y el periodo (Ep4-Hu30)."""
    d, proyectos = calcular(db, desde, hasta)
    periodo = f"{desde or 'inicio'} a {hasta or 'hoy'}"
    resumen = [
        ("Periodo", periodo), ("Proyectos registrados", d.proyectos), ("Postulaciones", d.postulaciones),
        ("Tasa de éxito de postulaciones", _pct(d.tasa_exito_postulaciones)),
        ("Recomendaciones generadas", d.recomendaciones_generadas), ("Recomendaciones aceptadas", d.recomendaciones_aceptadas),
        ("Recomendaciones descartadas", d.recomendaciones_anuladas),
        ("Aceptadas frente a generadas", _pct(d.tasa_aceptacion_recomendaciones)),
    ]
    hojas = [
        ("Resumen", ["Indicador", "Valor"], resumen),
        ("Por programa", ["Programa", "Proyectos"], [(c.clave, c.total) for c in d.por_programa]),
        ("Por área", ["Área", "Proyectos"], [(c.clave, c.total) for c in d.por_area]),
        ("Por estado", ["Estado", "Proyectos"], [(c.clave, c.total) for c in d.por_estado]),
        ("Por mes", ["Mes", "Proyectos", "Alianzas", "Alianzas aceptadas", "Postulaciones", "Seleccionadas"],
         [(m.mes, m.proyectos, m.alianzas, m.alianzas_aceptadas, m.postulaciones, m.postulaciones_aceptadas) for m in d.por_mes]),
        ("Proyectos", ["Título", "Área", "Estado", "Avance (%)", "Programa", "Responsable", "Registrado"],
         [(p.titulo, p.area.nombre, p.estado.value, p.avance, p.creado_por.programa if p.creado_por else "",
           p.creado_por.nombre if p.creado_por else "", p.creado_en.strftime("%Y-%m-%d"))
          for p in sorted(proyectos, key=lambda p: p.creado_en, reverse=True)]),
    ]
    registrar(db, admin, "reporte.exportar", "Reporte del panel (Excel)", f"Periodo {periodo}")
    db.commit()
    return excel.respuesta("reporte-panel-proyecta.xlsx", excel.libro(hojas, "Reporte del panel de Proyecta"))
