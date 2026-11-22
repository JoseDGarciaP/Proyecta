"""Archivos adjuntos a la ficha de un proyecto (Ep4-Hu22): PDF, DOCX, PNG o JPG hasta 10 MB."""

import mimetypes
import secrets
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.router import es_miembro
from app.modules.evidencias.router import MIME_DOCX, _es_docx_valido
from app.modules.proyectos.models import AdjuntoProyecto, Proyecto
from app.modules.proyectos.router import obtener_proyecto
from app.modules.proyectos.schemas import AdjuntoSalida
from app.modules.roles.servicio import puede

router = APIRouter(tags=["proyectos"])

PERMITIDOS = {
    "application/pdf": (".pdf", b"%PDF"),
    "image/png": (".png", b"\x89PNG\r\n\x1a\n"),
    "image/jpeg": (".jpg", b"\xff\xd8\xff"),
    MIME_DOCX: (".docx", b"PK\x03\x04"),
}


def carpeta() -> Path:
    ruta = Path(get_settings().archivos_dir) / "adjuntos"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _salida(a: AdjuntoProyecto) -> AdjuntoSalida:
    return AdjuntoSalida(id=a.id, nombre=a.nombre, tipo=a.tipo, tamano=a.tamano,
                         subido_por=a.subido_por.nombre if a.subido_por else "Usuario eliminado", creado_en=a.creado_en)


@router.get("/api/proyectos/{proyecto_id}/adjuntos", response_model=list[AdjuntoSalida])
def listar(proyecto_id: uuid.UUID, db: DbSession):
    obtener_proyecto(db, proyecto_id)
    filas = db.scalars(select(AdjuntoProyecto).where(AdjuntoProyecto.proyecto_id == proyecto_id)
                       .order_by(AdjuntoProyecto.creado_en.desc()))
    return [_salida(a) for a in filas]


@router.post("/api/proyectos/{proyecto_id}/adjuntos", response_model=AdjuntoSalida, status_code=status.HTTP_201_CREATED)
async def subir(proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession, archivo: UploadFile = File(...)):
    proyecto = obtener_proyecto(db, proyecto_id)
    if not es_miembro(db, proyecto, usuario.id) and not puede(db, usuario, "proyectos.moderar"):
        raise HTTPException(status_code=403, detail="Solo el equipo del proyecto puede adjuntar archivos")
    limite = get_settings().archivo_max_mb * 1024 * 1024
    contenido = await archivo.read(limite + 1)
    if len(contenido) > limite:
        raise HTTPException(status_code=413, detail=f"El archivo supera {get_settings().archivo_max_mb} MB")
    if not contenido:
        raise HTTPException(status_code=422, detail="El archivo está vacío")
    nombre = (archivo.filename or "").lower()
    tipo = (archivo.content_type or mimetypes.guess_type(nombre)[0] or "").lower()
    if tipo in ("", "application/octet-stream", "application/zip") and nombre.endswith(".docx"):
        tipo = MIME_DOCX
    if tipo not in PERMITIDOS:
        raise HTTPException(status_code=415, detail="Solo se aceptan PDF, DOCX, PNG o JPG")
    extension, firma = PERMITIDOS[tipo]
    if not contenido.startswith(firma) or (tipo == MIME_DOCX and not _es_docx_valido(contenido)):
        raise HTTPException(status_code=415, detail="El contenido del archivo no corresponde a un PDF, DOCX, PNG o JPG")
    ruta = f"{secrets.token_hex(16)}{extension}"
    (carpeta() / ruta).write_bytes(contenido)
    adjunto = AdjuntoProyecto(proyecto_id=proyecto.id, subido_por_id=usuario.id, nombre=(archivo.filename or f"archivo{extension}")[:255],
                              ruta=ruta, tipo=tipo, tamano=len(contenido))
    db.add(adjunto)
    db.commit()
    return _salida(adjunto)


def _obtener(db, adjunto_id: uuid.UUID) -> AdjuntoProyecto:
    adjunto = db.get(AdjuntoProyecto, adjunto_id)
    if adjunto is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return adjunto


@router.get("/api/adjuntos/{adjunto_id}/archivo")
def descargar(adjunto_id: uuid.UUID, db: DbSession):
    adjunto = _obtener(db, adjunto_id)
    ruta = carpeta() / adjunto.ruta
    if not ruta.exists():
        raise HTTPException(status_code=404, detail="El archivo ya no está disponible")
    return FileResponse(ruta, media_type=adjunto.tipo, filename=adjunto.nombre)


@router.delete("/api/adjuntos/{adjunto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(adjunto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession):
    adjunto = _obtener(db, adjunto_id)
    proyecto = db.get(Proyecto, adjunto.proyecto_id)
    if (proyecto is None or proyecto.creado_por_id != usuario.id) and adjunto.subido_por_id != usuario.id \
            and not puede(db, usuario, "proyectos.moderar"):
        raise HTTPException(status_code=403, detail="Solo el dueño del proyecto puede eliminar sus archivos")
    (carpeta() / adjunto.ruta).unlink(missing_ok=True)
    db.delete(adjunto)
    db.commit()
