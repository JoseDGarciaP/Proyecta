import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import Base, utcnow
from app.core.deps import DbSession, UsuarioActual
from app.modules.alianzas.models import EstadoSolicitud, Miembro, Solicitud
from app.modules.alianzas.router import es_miembro
from app.modules.chat.models import Lectura, LecturaSolicitud, Mensaje, MensajeBase, MensajeSolicitud
from app.modules.chat.schemas import Leido, MensajeEntrada, MensajeSalida, ResumenChat
from app.modules.proyectos.models import Proyecto
from app.modules.proyectos.router import obtener_proyecto
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(tags=["chat"])


class Conversacion:
    """Un hilo de mensajes: el chat de un proyecto o el de una solicitud. Comparten toda la lógica."""

    def __init__(self, modelo: type[MensajeBase], lectura: type[Base], campo: str, valor: uuid.UUID):
        self.modelo, self.lectura, self.campo, self.valor = modelo, lectura, campo, valor

    @property
    def filtro(self):
        return getattr(self.modelo, self.campo) == self.valor

    def listar(self, db: Session, yo: uuid.UUID, despues_de: int | None, cambios_desde: datetime | None,
               antes_de: int | None, limite: int) -> list[MensajeSalida]:
        M = self.modelo
        stmt = select(M).where(self.filtro)
        if despues_de is not None:
            condicion = M.id > despues_de
            if cambios_desde is not None:
                # >= para no perder cambios hechos en el mismo instante; el cliente los une por id.
                condicion = or_(condicion, M.modificado_en >= cambios_desde)
            mensajes = db.scalars(stmt.where(condicion).order_by(M.id).limit(limite)).all()
        else:
            if antes_de is not None:
                stmt = stmt.where(M.id < antes_de)
            mensajes = list(reversed(db.scalars(stmt.order_by(M.id.desc()).limit(limite)).all()))
        return [MensajeSalida.de(m, yo) for m in mensajes]

    def enviar(self, db: Session, autor: Usuario, texto: str) -> MensajeSalida:
        mensaje = self.modelo(**{self.campo: self.valor}, autor=autor, texto=texto)
        db.add(mensaje)
        db.flush()
        self.marcar_leido(db, autor.id, mensaje.id)  # lo propio no cuenta como no leído
        db.commit()
        return MensajeSalida.de(mensaje, autor.id)

    def obtener(self, db: Session, mensaje_id: int) -> MensajeBase:
        mensaje = db.get(self.modelo, mensaje_id)
        if mensaje is None or getattr(mensaje, self.campo) != self.valor or mensaje.eliminado:
            raise HTTPException(status_code=404, detail="Mensaje no encontrado")
        return mensaje

    def editar(self, db: Session, usuario: Usuario, mensaje_id: int, texto: str) -> MensajeSalida:
        mensaje = self.obtener(db, mensaje_id)
        if mensaje.autor_id != usuario.id:
            raise HTTPException(status_code=403, detail="Solo quien escribió el mensaje puede editarlo")
        mensaje.texto = texto
        mensaje.editado_en = mensaje.modificado_en = utcnow()
        db.commit()
        return MensajeSalida.de(mensaje, usuario.id)

    def eliminar(self, db: Session, usuario: Usuario, mensaje_id: int) -> None:
        """Quien lo escribió o un admin. Queda como «mensaje eliminado» para no romper el hilo."""
        mensaje = self.obtener(db, mensaje_id)
        if mensaje.autor_id != usuario.id and usuario.rol != Rol.ADMIN:
            raise HTTPException(status_code=403, detail="Solo quien escribió el mensaje puede eliminarlo")
        mensaje.eliminado = True
        mensaje.texto = ""
        mensaje.modificado_en = utcnow()
        db.commit()

    def marcar_leido(self, db: Session, usuario_id: uuid.UUID, hasta_id: int) -> None:
        lectura = db.get(self.lectura, (self.valor, usuario_id))
        if lectura is None:
            db.add(self.lectura(**{self.campo: self.valor}, usuario_id=usuario_id, ultimo_leido_id=hasta_id))
        elif hasta_id > lectura.ultimo_leido_id:  # nunca retrocede
            lectura.ultimo_leido_id = hasta_id

    def resumen(self, db: Session, yo: uuid.UUID) -> tuple[int, MensajeSalida | None]:
        """Mensajes de otros sin leer y el último mensaje."""
        M = self.modelo
        lectura = db.get(self.lectura, (self.valor, yo))
        no_leidos = db.scalar(select(func.count()).where(
            self.filtro, M.id > (lectura.ultimo_leido_id if lectura else 0),
            M.eliminado.is_(False), or_(M.autor_id.is_(None), M.autor_id != yo),
        )) or 0
        ultimo = db.scalars(select(M).where(self.filtro).order_by(M.id.desc()).limit(1)).first()
        return no_leidos, MensajeSalida.de(ultimo, yo) if ultimo else None


# ---- Chat del equipo de un proyecto ----------------------------------------------------------

def _chat_proyecto(db: Session, proyecto_id: uuid.UUID, usuario: Usuario) -> Conversacion:
    """El chat es privado: solo el responsable, los miembros y un admin (para moderar)."""
    proyecto = obtener_proyecto(db, proyecto_id)
    if usuario.rol != Rol.ADMIN and not es_miembro(db, proyecto, usuario.id):
        raise HTTPException(status_code=403, detail="El chat es solo para quienes hacen parte del proyecto")
    return Conversacion(Mensaje, Lectura, "proyecto_id", proyecto_id)


CURSORES = {
    "despues_de": Query(default=None, description="Solo los mensajes más nuevos que este id (para consultar cada pocos segundos)"),
    "cambios_desde": Query(default=None, description="Con `despues_de`: incluye también los editados o eliminados desde esta fecha (el mayor `modificado_en` que se tiene)"),
    "antes_de": Query(default=None, description="Los anteriores a este id (para cargar el historial)"),
    "limite": Query(default=50, ge=1, le=200),
}


@router.get("/api/proyectos/{proyecto_id}/mensajes", response_model=list[MensajeSalida])
def listar_mensajes(
    proyecto_id: uuid.UUID, usuario: UsuarioActual, db: DbSession,
    despues_de: int | None = CURSORES["despues_de"], cambios_desde: datetime | None = CURSORES["cambios_desde"],
    antes_de: int | None = CURSORES["antes_de"], limite: int = CURSORES["limite"],
):
    """Mensajes en orden cronológico. Sin cursores devuelve los últimos `limite`."""
    return _chat_proyecto(db, proyecto_id, usuario).listar(db, usuario.id, despues_de, cambios_desde, antes_de, limite)


@router.post("/api/proyectos/{proyecto_id}/mensajes", response_model=MensajeSalida, status_code=status.HTTP_201_CREATED)
def enviar_mensaje(proyecto_id: uuid.UUID, datos: MensajeEntrada, usuario: UsuarioActual, db: DbSession):
    return _chat_proyecto(db, proyecto_id, usuario).enviar(db, usuario, datos.texto)


@router.patch("/api/proyectos/{proyecto_id}/mensajes/{mensaje_id}", response_model=MensajeSalida)
def editar_mensaje(proyecto_id: uuid.UUID, mensaje_id: int, datos: MensajeEntrada, usuario: UsuarioActual, db: DbSession):
    return _chat_proyecto(db, proyecto_id, usuario).editar(db, usuario, mensaje_id, datos.texto)


@router.delete("/api/proyectos/{proyecto_id}/mensajes/{mensaje_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_mensaje(proyecto_id: uuid.UUID, mensaje_id: int, usuario: UsuarioActual, db: DbSession):
    _chat_proyecto(db, proyecto_id, usuario).eliminar(db, usuario, mensaje_id)


@router.post("/api/proyectos/{proyecto_id}/mensajes/leidos", status_code=status.HTTP_204_NO_CONTENT)
def marcar_leidos(proyecto_id: uuid.UUID, datos: Leido, usuario: UsuarioActual, db: DbSession):
    _chat_proyecto(db, proyecto_id, usuario).marcar_leido(db, usuario.id, datos.hasta_id)
    db.commit()


# ---- Conversación de una solicitud o invitación ----------------------------------------------

def _solicitud(db: Session, solicitud_id: uuid.UUID, usuario: Usuario) -> Solicitud:
    """Conversan quien pidió unirse (o fue invitado) y quien registró el proyecto; un admin puede leer."""
    solicitud = db.get(Solicitud, solicitud_id)
    if solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if usuario.rol != Rol.ADMIN and usuario.id not in (solicitud.usuario_id, solicitud.proyecto.creado_por_id):
        raise HTTPException(status_code=403, detail="Esta conversación es entre quien solicita y el responsable del proyecto")
    return solicitud


def _chat_solicitud(db: Session, solicitud_id: uuid.UUID, usuario: Usuario, escribir: bool = False) -> Conversacion:
    solicitud = _solicitud(db, solicitud_id, usuario)
    if escribir and solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise HTTPException(status_code=409, detail=f"La solicitud ya fue {solicitud.estado.value}: la conversación quedó cerrada")
    return Conversacion(MensajeSolicitud, LecturaSolicitud, "solicitud_id", solicitud_id)


@router.get("/api/alianzas/{solicitud_id}/mensajes", response_model=list[MensajeSalida])
def listar_mensajes_solicitud(
    solicitud_id: uuid.UUID, usuario: UsuarioActual, db: DbSession,
    despues_de: int | None = CURSORES["despues_de"], cambios_desde: datetime | None = CURSORES["cambios_desde"],
    antes_de: int | None = CURSORES["antes_de"], limite: int = CURSORES["limite"],
):
    return _chat_solicitud(db, solicitud_id, usuario).listar(db, usuario.id, despues_de, cambios_desde, antes_de, limite)


@router.post("/api/alianzas/{solicitud_id}/mensajes", response_model=MensajeSalida, status_code=status.HTTP_201_CREATED)
def enviar_mensaje_solicitud(solicitud_id: uuid.UUID, datos: MensajeEntrada, usuario: UsuarioActual, db: DbSession):
    """Solo mientras la solicitud está pendiente; después queda como historial."""
    return _chat_solicitud(db, solicitud_id, usuario, escribir=True).enviar(db, usuario, datos.texto)


@router.patch("/api/alianzas/{solicitud_id}/mensajes/{mensaje_id}", response_model=MensajeSalida)
def editar_mensaje_solicitud(solicitud_id: uuid.UUID, mensaje_id: int, datos: MensajeEntrada, usuario: UsuarioActual, db: DbSession):
    return _chat_solicitud(db, solicitud_id, usuario, escribir=True).editar(db, usuario, mensaje_id, datos.texto)


@router.delete("/api/alianzas/{solicitud_id}/mensajes/{mensaje_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_mensaje_solicitud(solicitud_id: uuid.UUID, mensaje_id: int, usuario: UsuarioActual, db: DbSession):
    _chat_solicitud(db, solicitud_id, usuario).eliminar(db, usuario, mensaje_id)


@router.post("/api/alianzas/{solicitud_id}/mensajes/leidos", status_code=status.HTTP_204_NO_CONTENT)
def marcar_leidos_solicitud(solicitud_id: uuid.UUID, datos: Leido, usuario: UsuarioActual, db: DbSession):
    _chat_solicitud(db, solicitud_id, usuario).marcar_leido(db, usuario.id, datos.hasta_id)
    db.commit()


# ---- Mis chats -------------------------------------------------------------------------------

@router.get("/api/chats", response_model=list[ResumenChat])
def mis_chats(usuario: UsuarioActual, db: DbSession):
    """Chats de mis proyectos y conversaciones de mis solicitudes, los más activos primero.

    Las conversaciones de solicitudes solo aparecen si ya tienen mensajes.
    """
    proyectos = db.scalars(
        select(Proyecto).outerjoin(Miembro, (Miembro.proyecto_id == Proyecto.id) & (Miembro.usuario_id == usuario.id))
        .where(or_(Proyecto.creado_por_id == usuario.id, Miembro.usuario_id.is_not(None)))
    ).unique().all()
    resumen = []
    for p in proyectos:
        no_leidos, ultimo = Conversacion(Mensaje, Lectura, "proyecto_id", p.id).resumen(db, usuario.id)
        resumen.append(ResumenChat(
            tipo="proyecto", proyecto_id=p.id, proyecto_titulo=p.titulo, solicitud_id=None,
            titulo=p.titulo, no_leidos=no_leidos, ultimo=ultimo,
        ))

    solicitudes = db.scalars(
        select(Solicitud).join(Solicitud.proyecto)
        .where(or_(Solicitud.usuario_id == usuario.id, Proyecto.creado_por_id == usuario.id))
        .where(select(MensajeSolicitud.id).where(MensajeSolicitud.solicitud_id == Solicitud.id).exists())
    ).unique().all()
    for s in solicitudes:
        no_leidos, ultimo = Conversacion(MensajeSolicitud, LecturaSolicitud, "solicitud_id", s.id).resumen(db, usuario.id)
        if usuario.id == s.usuario_id:
            responsable = db.get(Usuario, s.proyecto.creado_por_id) if s.proyecto.creado_por_id else None
            otro = responsable.nombre if responsable else "Responsable"
        else:
            otro = s.usuario.nombre
        resumen.append(ResumenChat(
            tipo="solicitud", proyecto_id=s.proyecto_id, proyecto_titulo=s.proyecto.titulo, solicitud_id=s.id,
            titulo=f"{otro} · {s.proyecto.titulo}", no_leidos=no_leidos, ultimo=ultimo,
        ))
    return sorted(resumen, key=lambda r: r.ultimo.enviado_en.timestamp() if r.ultimo else 0, reverse=True)
