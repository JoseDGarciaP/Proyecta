"""Historial personal con filtro por tipo y año, y su exportación a Excel (Ep4-Hu10, Ep4-Hu16)."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core import excel
from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.models import Miembro, Solicitud
from app.modules.aportes.models import Aporte
from app.modules.insignias.models import UsuarioInsignia
from app.modules.postulaciones.models import Postulacion
from app.modules.proyectos.models import Proyecto
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/usuarios/yo", tags=["usuarios"])

Tipo = Literal["proyecto", "alianza", "postulacion", "aporte", "logro"]
TIPOS: dict[str, str] = {"proyecto": "Proyecto", "alianza": "Alianza", "postulacion": "Postulación", "aporte": "Aporte",
                         "logro": "Logro"}


class Evento(BaseModel):
    tipo: Tipo
    fecha: datetime
    titulo: str
    detalle: str
    estado: str
    enlace: str


def eventos(db: Session, u: Usuario) -> list[Evento]:
    salida: list[Evento] = []
    for p in db.scalars(select(Proyecto).where(Proyecto.creado_por_id == u.id)).unique():
        salida.append(Evento(tipo="proyecto", fecha=p.creado_en, titulo=p.titulo, detalle=f"Registraste el proyecto · {p.area.nombre}",
                             estado=p.estado.value, enlace=f"/proyectos/{p.id}"))
    for s in db.scalars(select(Solicitud).where(Solicitud.usuario_id == u.id)).unique():
        que = "Pediste unirte a" if s.tipo.value == "solicitud" else "Te invitaron a"
        salida.append(Evento(tipo="alianza", fecha=s.creado_en, titulo=s.proyecto.titulo,
                             detalle=f"{que} «{s.proyecto.titulo}»" + (f" como {s.rol_propuesto}" if s.rol_propuesto else ""),
                             estado=s.estado.value, enlace=f"/proyectos/{s.proyecto_id}"))
    mis_proyectos = set(db.scalars(select(Miembro.proyecto_id).where(Miembro.usuario_id == u.id)))
    for p in db.scalars(select(Postulacion).join(Postulacion.proyecto).where(
            or_(Postulacion.usuario_id == u.id, Proyecto.creado_por_id == u.id, Postulacion.proyecto_id.in_(mis_proyectos)))).unique():
        salida.append(Evento(tipo="postulacion", fecha=p.creado_en, titulo=p.oportunidad.titulo,
                             detalle=f"«{p.proyecto.titulo}» postuló a {p.oportunidad.entidad or 'la convocatoria'}",
                             estado=p.estado.value, enlace=f"/proyectos/{p.proyecto_id}"))
    for a in db.scalars(select(Aporte).where(Aporte.usuario_id == u.id)):
        horas = f" · {a.horas} h" if a.horas else ""
        salida.append(Evento(tipo="aporte", fecha=a.creado_en, titulo=a.tipo, detalle=f"{a.descripcion[:140]}{horas}",
                             estado=a.estado.value, enlace=f"/proyectos/{a.proyecto_id}"))
    for ui in db.scalars(select(UsuarioInsignia).where(UsuarioInsignia.usuario_id == u.id)):
        salida.append(Evento(tipo="logro", fecha=ui.otorgada_en, titulo=ui.insignia.nombre, detalle=ui.motivo or "Insignia obtenida",
                             estado="obtenida", enlace="/perfil#logros"))
    return sorted(salida, key=lambda e: e.fecha, reverse=True)


def _filtrar(lista: list[Evento], tipo: str | None, anio: int | None) -> list[Evento]:
    return [e for e in lista if (tipo is None or e.tipo == tipo) and (anio is None or e.fecha.year == anio)]


@router.get("/historial", response_model=list[Evento])
def historial(usuario: UsuarioActual, db: DbSession, tipo: Tipo | None = None, anio: int | None = Query(default=None, ge=2000)):
    return _filtrar(eventos(db, usuario), tipo, anio)


@router.get("/historial.xlsx")
def historial_excel(usuario: UsuarioActual, db: DbSession, tipo: Tipo | None = None, anio: int | None = Query(default=None, ge=2000)):
    filas = [(e.fecha.strftime("%Y-%m-%d"), TIPOS[e.tipo], e.titulo, e.detalle, e.estado)
             for e in _filtrar(eventos(db, usuario), tipo, anio)]
    contenido = excel.libro([("Historial", ["Fecha", "Tipo", "Título", "Detalle", "Estado"], filas)],
                            f"Historial de {usuario.nombre} en Proyecta")
    return excel.respuesta("mi-historial-proyecta.xlsx", contenido)
