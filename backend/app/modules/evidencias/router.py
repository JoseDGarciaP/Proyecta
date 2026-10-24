import mimetypes
import secrets
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import utcnow
from app.core.deps import Admin, DbSession, UsuarioActual, requiere
from app.modules.admin.bitacora import registrar
from app.modules.alianzas.router import es_miembro
from app.modules.evidencias.models import EstadoEvidencia, Evidencia, TipoEvidencia
from app.modules.experiencia.models import AccionXP
from app.modules.experiencia.servicio import sumar
from app.modules.notificaciones.models import TipoNotificacion
from app.modules.notificaciones.servicio import notificar
from app.modules.proyectos.models import Proyecto
from app.modules.roles.servicio import puede, usuarios_con_permiso

router = APIRouter(tags=["evidencias"])
admin = APIRouter(prefix="/api/admin/evidencias", tags=["administración"], dependencies=[Depends(requiere("admin.evidencias"))])

# Tipo de archivo aceptado → (extensión, firma de los primeros bytes)
PERMITIDOS = {
    "application/pdf": (".pdf", [b"%PDF"]),
    "image/png": (".png", [b"\x89PNG\r\n\x1a\n"]),
    "image/jpeg": (".jpg", [b"\xff\xd8\xff"]),
    "image/webp": (".webp", [b"RIFF"]),
}


class EvidenciaSalida(BaseModel):
    id: uuid.UUID
    usuario_id: uuid.UUID
    usuario_nombre: str
    proyecto_id: uuid.UUID | None
    proyecto_titulo: str | None
    titulo: str
    descripcion: str
    tipo: TipoEvidencia
    archivo_nombre: str
    archivo_tipo: str
    archivo_tamano: int
    estado: EstadoEvidencia
    xp_otorgada: int
    comentario: str
    revisada_por: str | None
    revisada_en: datetime | None
    creado_en: datetime

    @classmethod
    def de(cls, e: Evidencia) -> "EvidenciaSalida":
        utc = utcnow().tzinfo
        return cls(id=e.id, usuario_id=e.usuario_id, usuario_nombre=e.usuario.nombre, proyecto_id=e.proyecto_id,
                   proyecto_titulo=e.proyecto.titulo if e.proyecto else None, titulo=e.titulo, descripcion=e.descripcion,
                   tipo=e.tipo, archivo_nombre=e.archivo_nombre, archivo_tipo=e.archivo_tipo, archivo_tamano=e.archivo_tamano,
                   estado=e.estado, xp_otorgada=e.xp_otorgada, comentario=e.comentario,
                   revisada_por=e.revisada_por.nombre if e.revisada_por else None,
                   revisada_en=e.revisada_en.replace(tzinfo=utc) if e.revisada_en and not e.revisada_en.tzinfo else e.revisada_en,
                   creado_en=e.creado_en.replace(tzinfo=utc) if not e.creado_en.tzinfo else e.creado_en)


class Revision(BaseModel):
    aprobar: bool
    puntos: int | None = Field(default=None, ge=0, le=10_000, description="XP a otorgar (por defecto, la de «evidencia_aprobada»)")
    comentario: str = Field(default="", max_length=1000)


def carpeta() -> Path:
    ruta = Path(get_settings().archivos_dir) / "evidencias"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _puede_ver(db: Session, usuario, e: Evidencia) -> bool:
    if e.usuario_id == usuario.id or puede(db, usuario, "admin.evidencias"):
        return True
    if e.proyecto and es_miembro(db, e.proyecto, usuario.id):
        return True
    return e.estado == EstadoEvidencia.APROBADA and puede(db, usuario, "usuarios.ver")


@router.post("/api/evidencias", response_model=EvidenciaSalida, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requiere("evidencias.subir"))])
async def subir(usuario: UsuarioActual, db: DbSession, tareas: BackgroundTasks,
                archivo: UploadFile = File(...), titulo: str = Form(min_length=3, max_length=200),
                descripcion: str = Form(default="", max_length=1500), tipo: TipoEvidencia = Form(default=TipoEvidencia.CERTIFICADO),
                proyecto_id: uuid.UUID | None = Form(default=None)):
    proyecto = None
    if proyecto_id:
        proyecto = db.get(Proyecto, proyecto_id)
        if proyecto is None:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        if not es_miembro(db, proyecto, usuario.id):
            raise HTTPException(status_code=403, detail="Solo el equipo puede adjuntar evidencias a este proyecto")
    limite = get_settings().archivo_max_mb * 1024 * 1024
    contenido = await archivo.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(status_code=413, detail=f"El archivo supera {get_settings().archivo_max_mb} MB")
    if not contenido:
        raise HTTPException(status_code=422, detail="El archivo está vacío")
    tipo_mime = (archivo.content_type or mimetypes.guess_type(archivo.filename or "")[0] or "").lower()
    if tipo_mime not in PERMITIDOS:
        raise HTTPException(status_code=415, detail="Sube un PDF o una imagen (PNG, JPG o WEBP)")
    extension, firmas = PERMITIDOS[tipo_mime]
    if not any(contenido.startswith(f) for f in firmas) or (tipo_mime == "image/webp" and contenido[8:12] != b"WEBP"):
        raise HTTPException(status_code=415, detail="El contenido del archivo no corresponde a un PDF o una imagen")
    nombre_disco = f"{secrets.token_hex(16)}{extension}"
    (carpeta() / nombre_disco).write_bytes(contenido)
    evidencia = Evidencia(usuario_id=usuario.id, proyecto_id=proyecto.id if proyecto else None, titulo=titulo.strip(),
                          descripcion=descripcion.strip(), tipo=tipo, archivo_nombre=(archivo.filename or f"archivo{extension}")[:255],
                          archivo_ruta=nombre_disco, archivo_tipo=tipo_mime, archivo_tamano=len(contenido))
    db.add(evidencia)
    db.flush()
    for revisor in usuarios_con_permiso(db, "admin.evidencias"):
        if revisor.id != usuario.id:
            notificar(db, revisor, TipoNotificacion.REVISION, f"Nueva evidencia por revisar: «{evidencia.titulo}»",
                      f"De {usuario.nombre}" + (f" · proyecto «{proyecto.titulo}»" if proyecto else ""), "/admin/evidencias", tareas,
                      boton="Revisar evidencias")
    db.commit()
    db.refresh(evidencia)
    return EvidenciaSalida.de(evidencia)


@router.get("/api/evidencias/mias", response_model=list[EvidenciaSalida])
def mis_evidencias(usuario: UsuarioActual, db: DbSession):
    return [EvidenciaSalida.de(e) for e in db.scalars(select(Evidencia).where(Evidencia.usuario_id == usuario.id)
                                                      .order_by(Evidencia.creado_en.desc())).unique()]


@router.get("/api/proyectos/{proyecto_id}/evidencias", response_model=list[EvidenciaSalida])
def evidencias_proyecto(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    proyecto = db.get(Proyecto, proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    stmt = select(Evidencia).where(Evidencia.proyecto_id == proyecto_id)
    if not (es_miembro(db, proyecto, usuario.id) or puede(db, usuario, "admin.evidencias")):
        stmt = stmt.where(Evidencia.estado == EstadoEvidencia.APROBADA)
    return [EvidenciaSalida.de(e) for e in db.scalars(stmt.order_by(Evidencia.creado_en.desc())).unique()]


@router.get("/api/evidencias/{evidencia_id}/archivo")
def descargar(evidencia_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    e = db.get(Evidencia, evidencia_id)
    if e is None or not _puede_ver(db, usuario, e):
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    ruta = carpeta() / e.archivo_ruta
    if not ruta.is_file():
        raise HTTPException(status_code=410, detail="El archivo ya no está disponible")
    return FileResponse(ruta, media_type=e.archivo_tipo, filename=e.archivo_nombre, content_disposition_type="inline")


@router.delete("/api/evidencias/{evidencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(evidencia_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    e = db.get(Evidencia, evidencia_id)
    if e is None or e.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    if e.estado == EstadoEvidencia.APROBADA:
        raise HTTPException(status_code=409, detail="Una evidencia aprobada no se puede eliminar")
    (carpeta() / e.archivo_ruta).unlink(missing_ok=True)
    db.delete(e)
    db.commit()


# ---- Revisión --------------------------------------------------------------------------------

@admin.get("", response_model=list[EvidenciaSalida])
def listar(db: DbSession, estado: EstadoEvidencia | None = None, limite: int = Query(default=100, le=500)):
    stmt = select(Evidencia)
    if estado:
        stmt = stmt.where(Evidencia.estado == estado)
    return [EvidenciaSalida.de(e) for e in db.scalars(stmt.order_by(Evidencia.creado_en.desc()).limit(limite)).unique()]


@admin.post("/{evidencia_id}/revisar", response_model=EvidenciaSalida)
def revisar(evidencia_id: uuid.UUID, datos: Revision, yo: Admin, db: DbSession, tareas: BackgroundTasks):
    e = db.get(Evidencia, evidencia_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    if e.estado != EstadoEvidencia.PENDIENTE:
        raise HTTPException(status_code=409, detail=f"Ya fue {e.estado.value}")
    if not datos.aprobar and not datos.comentario.strip():
        raise HTTPException(status_code=422, detail="Explica por qué se rechaza")
    e.comentario, e.revisada_por_id, e.revisada_en = datos.comentario.strip(), yo.id, utcnow()
    if datos.aprobar:
        sugerido = db.get(AccionXP, "evidencia_aprobada")
        puntos = datos.puntos if datos.puntos is not None else (sugerido.puntos if sugerido else 0)
        e.estado, e.xp_otorgada = EstadoEvidencia.APROBADA, puntos
        if puntos:
            sumar(db, e.usuario, "evidencia", str(e.id), f"Evidencia aprobada: «{e.titulo}»", tareas, puntos=puntos, por=yo)
        titulo = f"Aprobaron tu evidencia «{e.titulo}»" + (f": +{puntos} XP" if puntos else "")
    else:
        e.estado = EstadoEvidencia.RECHAZADA
        titulo = f"Tu evidencia «{e.titulo}» no fue aprobada"
    notificar(db, e.usuario, TipoNotificacion.EVIDENCIA, titulo, e.comentario, "/perfil#evidencias", tareas,
              detalles=[("Evidencia", e.titulo), ("Estado", e.estado.value)] + ([("XP", str(e.xp_otorgada))] if e.xp_otorgada else [])
              + ([("Comentario", e.comentario)] if e.comentario else []), boton="Ver mis evidencias", parrafos=[])
    registrar(db, yo, "evidencia.revisar", f"{e.titulo} ({e.usuario.nombre})", f"{e.estado.value} · {e.xp_otorgada} XP")
    if datos.aprobar:
        from app.modules.insignias.servicio import evaluar
        evaluar(db, e.usuario, tareas)
    db.commit()
    return EvidenciaSalida.de(e)
