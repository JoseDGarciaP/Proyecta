import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import utcnow
from app.core.deps import Admin, DbSession, UsuarioActual, get_current_user, requiere
from app.modules.admin.bitacora import registrar
from app.modules.insignias import servicio
from app.modules.insignias.models import TIPOS, Insignia, UsuarioInsignia
from app.modules.insignias.schemas import (
    CriterioSalida, EnProgreso, Evaluacion, InsigniaBreve, InsigniaEntrada, InsigniaSalida, MisLogros, Opciones,
    OtorgadaSalida, Otorgamiento, OtorgamientoVarios, ProgresoCondicion, PuestoRanking, ResultadoVarios,
)
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/insignias", tags=["insignias"], dependencies=[Depends(get_current_user)])
admin = APIRouter(prefix="/api/admin/insignias", tags=["administración"], dependencies=[Depends(requiere("admin.insignias"))])


def _conteo(db: Session, insignia_id: int) -> int:
    return db.scalar(select(func.count()).where(UsuarioInsignia.insignia_id == insignia_id, servicio.vigente_ahora())) or 0


def _salida(db: Session, i: Insignia) -> InsigniaSalida:
    s = InsigniaSalida.model_validate(i)
    s.otorgadas = _conteo(db, i.id)
    s.texto_regla = servicio.texto_regla(db, i)
    return s


def _ordenadas(db: Session, solo_activas: bool = True):
    stmt = select(Insignia).order_by(Insignia.orden, Insignia.nombre)
    if solo_activas:
        stmt = stmt.where(Insignia.activo.is_(True))
    return db.scalars(stmt).all()


@router.get("", response_model=list[InsigniaSalida])
def catalogo(db: DbSession):
    """Todas las insignias activas: cómo se ganan y cuántas personas las tienen."""
    return [_salida(db, i) for i in _ordenadas(db)]


@router.get("/opciones", response_model=Opciones)
def opciones():
    return Opciones(
        criterios=[CriterioSalida(clave=k, nombre=c.nombre, unidad=c.unidad, valor=c.valor, binario=c.binario, grupo=c.grupo)
                   for k, c in servicio.CRITERIOS.items()],
        iconos=servicio.ICONOS, colores=servicio.COLORES, tipos=TIPOS)


@router.get("/mias", response_model=MisLogros)
def mis_logros(usuario: UsuarioActual, db: DbSession):
    vigentes = servicio.vigentes(db, [usuario.id]).get(usuario.id, [])
    vencidas = servicio.vencidas(db, usuario.id)
    tengo = {f.insignia_id for f in vigentes} | {f.insignia_id for f in vencidas}
    en_progreso, manuales, cache = [], [], {}
    for i in _ordenadas(db):
        if i.id in tengo:
            continue
        if i.automatica:
            condiciones = [ProgresoCondicion(texto=servicio.texto_condicion(db, c), actual=min(actual, c.get("umbral") or 1),
                                             umbral=c.get("umbral") or 1)
                           for c, actual in servicio.progreso(db, usuario, i, cache)]
            fracciones = [c.actual / c.umbral for c in condiciones]
            avance = (sum(fracciones) / len(fracciones)) if i.modo == "todas" else max(fracciones)
            en_progreso.append(EnProgreso(insignia=_salida(db, i), modo=i.modo, condiciones=condiciones, avance=round(avance, 3)))
        else:
            manuales.append(_salida(db, i))
    en_progreso.sort(key=lambda e: e.avance, reverse=True)
    return MisLogros(obtenidas=[InsigniaBreve.de(f) for f in vigentes], en_progreso=en_progreso, manuales_disponibles=manuales,
                     vencidas=[InsigniaBreve.de(f) for f in vencidas])


@router.get("/de", response_model=dict[str, list[InsigniaBreve]])
def insignias_de(db: DbSession, ids: str = Query(description="ids de usuario separados por coma (máx. 100)")):
    """Para mostrarlas junto al nombre en fichas, miembros y sugerencias."""
    lista = []
    for x in ids.split(",")[:100]:
        try:
            lista.append(uuid.UUID(x.strip()))
        except ValueError:
            continue
    return {str(uid): [InsigniaBreve.de(f) for f in filas] for uid, filas in servicio.vigentes(db, lista).items()}


@router.get("/ranking", response_model=list[PuestoRanking], dependencies=[Depends(requiere("usuarios.ver"))])
def ranking(db: DbSession, limite: int = Query(default=20, ge=1, le=100)):
    total = func.count(UsuarioInsignia.id).label("total")
    filas = db.execute(
        select(Usuario, total).join(UsuarioInsignia, UsuarioInsignia.usuario_id == Usuario.id)
        .join(Insignia, Insignia.id == UsuarioInsignia.insignia_id)
        .where(Usuario.activo.is_(True), servicio.vigente_ahora(), Insignia.activo.is_(True))
        .group_by(Usuario.id).order_by(total.desc(), func.min(UsuarioInsignia.otorgada_en)).limit(limite)
    ).unique().all()
    por_usuario = servicio.vigentes(db, [u.id for u, _ in filas])
    salida, posicion, anterior = [], 0, None
    for k, (u, n) in enumerate(filas, start=1):
        if n != anterior:
            posicion, anterior = k, n  # empates comparten puesto
        salida.append(PuestoRanking(posicion=posicion, usuario_id=u.id, nombre=u.nombre, rol_nombre=u.rol_nombre,
                                    programa=u.programa, total=n,
                                    insignias=[InsigniaBreve.de(f) for f in por_usuario.get(u.id, [])]))
    return salida


# ---- Administración --------------------------------------------------------------------------

def _validar(db: Session, datos: InsigniaEntrada) -> dict:
    from app.modules.catalogo.models import Area, Ods
    from app.modules.roles.models import RolUsuario

    if datos.icono not in servicio.ICONOS:
        raise HTTPException(status_code=422, detail="Ícono no válido")
    if datos.color not in servicio.COLORES:
        raise HTTPException(status_code=422, detail="Color no válido")
    valores = datos.model_dump(exclude={"reglas"})
    if datos.reglas:
        condiciones = []
        for c in datos.reglas.condiciones:
            criterio = servicio.CRITERIOS.get(c.criterio)
            if criterio is None:
                raise HTTPException(status_code=422, detail=f"Requisito no válido: {c.criterio}")
            valor = (c.valor or "").strip() or None
            if criterio.valor and not valor:
                raise HTTPException(status_code=422, detail=f"«{criterio.nombre}» necesita que elijas un valor")
            if criterio.valor == "area" and not db.scalar(select(Area.id).where(Area.nombre == valor)):
                raise HTTPException(status_code=422, detail=f"El área «{valor}» no existe")
            if criterio.valor == "ods" and not (valor.isdigit() and db.get(Ods, int(valor))):
                raise HTTPException(status_code=422, detail="Elige un ODS del 1 al 17")
            if criterio.valor == "rol" and not db.get(RolUsuario, valor):
                raise HTTPException(status_code=422, detail="Ese rol no existe")
            condiciones.append({"criterio": c.criterio, "umbral": 1 if criterio.binario else c.umbral,
                                "valor": valor if criterio.valor else None})
        valores["reglas"] = {"modo": datos.reglas.modo, "condiciones": condiciones}
    else:
        valores["reglas"] = None
    valores["nombre"] = datos.nombre.strip()
    valores["entidad"] = datos.entidad.strip()
    return valores


def _nombre_libre(db: Session, nombre: str, excepto: int | None = None) -> None:
    existe = db.scalar(select(Insignia.id).where(func.lower(Insignia.nombre) == nombre.strip().lower()))
    if existe and existe != excepto:
        raise HTTPException(status_code=409, detail=f"Ya existe la insignia «{nombre}»")


def _obtener(db: Session, insignia_id: int) -> Insignia:
    insignia = db.get(Insignia, insignia_id)
    if insignia is None:
        raise HTTPException(status_code=404, detail="Insignia no encontrada")
    return insignia


@admin.get("", response_model=list[InsigniaSalida])
def listar_admin(db: DbSession):
    return [_salida(db, i) for i in _ordenadas(db, solo_activas=False)]


@admin.post("", response_model=InsigniaSalida, status_code=status.HTTP_201_CREATED)
def crear(datos: InsigniaEntrada, yo: Admin, db: DbSession):
    _nombre_libre(db, datos.nombre)
    insignia = Insignia(**_validar(db, datos))
    db.add(insignia)
    registrar(db, yo, "insignia.crear", insignia.nombre, servicio.texto_regla(db, insignia))
    db.commit()
    if insignia.automatica and insignia.activo:
        servicio.evaluar_todos(db)  # quienes ya cumplen la regla la reciben de una vez
    return _salida(db, insignia)


@admin.put("/{insignia_id}", response_model=InsigniaSalida)
def editar(insignia_id: int, datos: InsigniaEntrada, yo: Admin, db: DbSession):
    insignia = _obtener(db, insignia_id)
    _nombre_libre(db, datos.nombre, insignia.id)
    for campo, valor in _validar(db, datos).items():
        setattr(insignia, campo, valor)
    registrar(db, yo, "insignia.editar", insignia.nombre,
              f"{'activa' if insignia.activo else 'inactiva'} · {servicio.texto_regla(db, insignia)}")
    db.commit()
    if insignia.automatica and insignia.activo:
        servicio.evaluar_todos(db)
    return _salida(db, insignia)


@admin.delete("/{insignia_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(insignia_id: int, yo: Admin, db: DbSession):
    insignia = _obtener(db, insignia_id)
    registrar(db, yo, "insignia.eliminar", insignia.nombre, f"La tenían {_conteo(db, insignia.id)} personas")
    db.delete(insignia)
    db.commit()


class Candidato(BaseModel):
    id: uuid.UUID
    nombre: str
    email: str
    rol_nombre: str


class ProyectoCandidato(BaseModel):
    id: uuid.UUID
    titulo: str
    equipo: int


@admin.get("/proyectos", response_model=list[ProyectoCandidato])
def proyectos_para_otorgar(db: DbSession, q: str = Query(default="", max_length=100)):
    """Para condecorar a todo un equipo."""
    from app.modules.alianzas.models import Miembro
    from app.modules.proyectos.models import Proyecto

    stmt = select(Proyecto).order_by(Proyecto.titulo).limit(15)
    if q.strip():
        stmt = stmt.where(Proyecto.titulo.ilike(f"%{q.strip()}%"))
    return [ProyectoCandidato(id=p.id, titulo=p.titulo,
                              equipo=(1 if p.creado_por_id else 0) + (db.scalar(select(func.count()).where(Miembro.proyecto_id == p.id)) or 0))
            for p in db.scalars(stmt).unique()]


@admin.get("/candidatos", response_model=list[Candidato])
def candidatos(db: DbSession, q: str = Query(min_length=2)):
    """Buscar a quién otorgar una insignia (sin necesitar el permiso de gestionar usuarios)."""
    patron = f"%{q.strip()}%"
    usuarios = db.scalars(select(Usuario).where(Usuario.activo.is_(True), or_(Usuario.nombre.ilike(patron), Usuario.email.ilike(patron)))
                          .order_by(Usuario.nombre).limit(10)).unique().all()
    return [Candidato(id=u.id, nombre=u.nombre, email=u.email, rol_nombre=u.rol_nombre) for u in usuarios]


@admin.get("/{insignia_id}/otorgadas", response_model=list[OtorgadaSalida])
def otorgadas(insignia_id: int, db: DbSession):
    _obtener(db, insignia_id)
    filas = db.scalars(select(UsuarioInsignia).where(UsuarioInsignia.insignia_id == insignia_id)
                       .order_by(UsuarioInsignia.retirada_en.is_not(None), UsuarioInsignia.otorgada_en.desc())).all()
    ahora = utcnow()

    def estado(f) -> str:
        if f.retirada_en:
            return "retirada"
        vence = f.vence_en.replace(tzinfo=ahora.tzinfo) if f.vence_en and f.vence_en.tzinfo is None else f.vence_en
        return "vencida" if vence and vence <= ahora else "vigente"

    return [OtorgadaSalida(usuario_id=f.usuario_id, nombre=f.usuario.nombre, email=f.usuario.email, motivo=f.motivo,
                           automatica=f.automatica, otorgada_por=f.otorgada_por.nombre if f.otorgada_por else None,
                           otorgada_en=f.otorgada_en, fecha_evento=f.fecha_evento, vence_en=f.vence_en,
                           retirada_en=f.retirada_en, estado=estado(f)) for f in filas]


@admin.post("/{insignia_id}/otorgar", response_model=InsigniaBreve)
def otorgar(insignia_id: int, datos: Otorgamiento, yo: Admin, db: DbSession, tareas: BackgroundTasks):
    insignia = _obtener(db, insignia_id)
    if not insignia.activo:
        raise HTTPException(status_code=409, detail="La insignia está desactivada")
    usuario = db.get(Usuario, datos.usuario_id)
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if _la_tiene(db, usuario.id, insignia.id):
        raise HTTPException(status_code=409, detail=f"{usuario.nombre} ya tiene esta insignia")
    fila = servicio.otorgar(db, usuario, insignia, datos.motivo.strip(), yo, tareas, datos.fecha_evento, datos.vence_en)
    registrar(db, yo, "insignia.otorgar", f"{insignia.nombre} → {usuario.nombre}", datos.motivo.strip())
    db.commit()
    return InsigniaBreve.de(fila)


def _la_tiene(db: Session, usuario_id, insignia_id: int) -> bool:
    return bool(db.scalar(select(UsuarioInsignia.id).where(UsuarioInsignia.usuario_id == usuario_id,
                                                           UsuarioInsignia.insignia_id == insignia_id, servicio.vigente_ahora())))


@admin.post("/{insignia_id}/otorgar-varios", response_model=ResultadoVarios)
def otorgar_varios(insignia_id: int, datos: OtorgamientoVarios, yo: Admin, db: DbSession, tareas: BackgroundTasks):
    """Condecorar de una vez a varias personas o a todo el equipo de un proyecto."""
    from app.modules.alianzas.models import Miembro
    from app.modules.proyectos.models import Proyecto

    insignia = _obtener(db, insignia_id)
    if not insignia.activo:
        raise HTTPException(status_code=409, detail="La insignia está desactivada")
    ids = list(dict.fromkeys(datos.usuario_ids))
    if datos.proyecto_id:
        proyecto = db.get(Proyecto, datos.proyecto_id)
        if proyecto is None:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        equipo = [proyecto.creado_por_id, *db.scalars(select(Miembro.usuario_id).where(Miembro.proyecto_id == proyecto.id))]
        ids += [i for i in equipo if i and i not in ids]
    if not ids:
        raise HTTPException(status_code=422, detail="Elige al menos una persona o un proyecto")
    otorgadas, ya = [], []
    for uid in ids:
        usuario = db.get(Usuario, uid)
        if usuario is None or not usuario.activo:
            continue
        if _la_tiene(db, usuario.id, insignia.id):
            ya.append(usuario.nombre)
            continue
        servicio.otorgar(db, usuario, insignia, datos.motivo.strip(), yo, tareas, datos.fecha_evento, datos.vence_en)
        otorgadas.append(usuario.nombre)
    registrar(db, yo, "insignia.otorgar", f"{insignia.nombre} → {len(otorgadas)} personas",
              f"{datos.motivo.strip()} · {', '.join(otorgadas)}")
    db.commit()
    return ResultadoVarios(otorgadas=otorgadas, ya_tenian=ya)


@admin.delete("/{insignia_id}/otorgadas/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def retirar(insignia_id: int, usuario_id: uuid.UUID, yo: Admin, db: DbSession):
    """La retira sin borrar el historial; una regla automática no la vuelve a dar (se puede otorgar de nuevo a mano)."""
    fila = db.scalar(select(UsuarioInsignia).where(UsuarioInsignia.usuario_id == usuario_id,
                                                   UsuarioInsignia.insignia_id == insignia_id,
                                                   servicio.vigente_ahora()))
    if fila is None:
        raise HTTPException(status_code=404, detail="Esa persona no tiene la insignia")
    fila.retirada_en = utcnow()
    registrar(db, yo, "insignia.retirar", f"{fila.insignia.nombre} ← {fila.usuario.nombre}")
    db.commit()


@admin.post("/evaluar", response_model=Evaluacion)
def evaluar(yo: Admin, db: DbSession):
    """Revisa a todas las personas y entrega las insignias automáticas que ya cumplen."""
    n = servicio.evaluar_todos(db)
    registrar(db, yo, "insignia.evaluar", "Revisión de logros", f"{n} insignias otorgadas")
    db.commit()
    return Evaluacion(otorgadas=n)
