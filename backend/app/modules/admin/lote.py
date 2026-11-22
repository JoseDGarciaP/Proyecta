"""Carga de proyectos por lote desde el Excel de respuestas del formulario de registro.

Flujo: el admin sube el archivo (`/previa`), revisa y corrige las filas (`/revisar`) y confirma (`/confirmar`).
Por cada correo nuevo se crea una cuenta de estudiante ya verificada y se le envía un único correo para elegir
su contraseña; a quien ya tenía cuenta solo se le avisa que se registraron proyectos a su nombre. Crear los
proyectos no genera otros avisos ni correos (XP e insignias se suman en silencio).
"""

import io
import re
import secrets
import unicodedata
import uuid
from collections import defaultdict
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import correo
from app.core.config import get_settings
from app.core.deps import Admin, DbSession, requiere
from app.core.security import create_token, hash_password, huella_password
from app.modules.admin.bitacora import registrar
from app.modules.auth.router import validar_correo
from app.modules.catalogo.models import Area, Ods
from app.modules.notificaciones.servicio import silencio
from app.modules.parametros import ajustes as ajustes_srv
from app.modules.proyectos.models import Estado, Proyecto
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/admin/lote", tags=["administración"], dependencies=[Depends(requiere("admin.usuarios"))])

MAX_BYTES = 5 * 1024 * 1024
MAX_FILAS = 500
RESUMEN_MAX = 300  # el mismo límite de ProyectoEntrada y del formulario de la interfaz
ODS_EDUCACION = 4
AREA_EDUCACION = "educacion"

# Columnas del formulario: se reconocen por una frase de su encabezado (sin tildes ni mayúsculas).
COLUMNAS = {
    "titulo": "nombre oficial",
    "resumen": "una sola frase",
    "descripcion": "detalla el contexto",
    "area": "seleccione el area",
    "estado": "estado actual",
    "lider": "nombre del lider",
    "coautores": "coautores",
    "presupuesto": "presupuesto",
    "avance": "grado de cumplimiento",
    "fecha_inicio": "arrancaron",
    "fecha_fin": "finalizar",
    "ods": "los ods",
    "necesidades": "recursos le hacen falta",
    "etiquetas": "terminos clave",
    "correo": "correo electronico",
}
OBLIGATORIAS = ("titulo", "resumen", "area", "estado", "lider", "correo")

ESTADOS = {
    "idea": Estado.IDEA,
    "formulacion": Estado.FORMULACION,
    "ejecucion": Estado.EJECUCION,
    "finalizado": Estado.FINALIZADO,
    "pausado": Estado.PAUSADO,
}
# Avance esperado según el estado (mínimo, máximo, valor si el informado no cuadra).
RANGO_AVANCE = {
    Estado.IDEA: (0, 20, 10),
    Estado.FORMULACION: (21, 50, 35),
    Estado.EJECUCION: (51, 99, 75),
    Estado.FINALIZADO: (100, 100, 100),
}
NOMBRE_ESTADO = {
    Estado.IDEA: "Idea", Estado.FORMULACION: "En formulación", Estado.EJECUCION: "En ejecución",
    Estado.FINALIZADO: "Finalizado", Estado.PAUSADO: "Pausado",
}


class FilaLote(BaseModel):
    fila: int  # número de fila en el Excel (la 1 es el encabezado)
    incluir: bool = True
    correo: str = ""
    nombre_cuenta: str = ""
    titulo: str = ""
    resumen: str = ""
    descripcion: str = ""
    necesidades: str = ""
    area: str = ""
    estado: Estado = Estado.IDEA
    avance: int = Field(default=0, ge=0, le=100)
    presupuesto: int = Field(default=0, ge=0)
    lider: str = ""
    equipo: list[str] = []
    etiquetas: list[str] = []
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    ods: list[int] = []
    # Los calcula el servidor en cada revisión:
    cuenta: Literal["nueva", "existente", ""] = ""
    errores: list[str] = []
    avisos: list[str] = []


class ResultadoLote(BaseModel):
    proyectos: int
    cuentas_nuevas: int
    cuentas_existentes: int
    correos: int


# ---- Lectura del archivo ----------------------------------------------------------------------

def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes).strip().lower()


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return re.sub(r"[ \t]+", " ", str(valor)).strip().strip('"').strip()


def _entero(valor) -> int | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return int(valor)
    digitos = re.sub(r"[^\d]", "", str(valor).split(",")[0])
    return int(digitos) if digitos else None


def _fecha(valor) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = _texto(valor)
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(texto[:10], formato).date()
        except ValueError:
            continue
    return None


def _lista(valor) -> list[str]:
    partes = re.split(r"[,;\n]", _texto(valor))
    vistos, salida = set(), []
    for p in partes:
        p = p.strip(" .`'\"")
        if p and normalizar(p) not in vistos:
            vistos.add(normalizar(p))
            salida.append(p)
    return salida


def leer_excel(contenido: bytes) -> list[dict]:
    from openpyxl import load_workbook

    try:
        libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception as error:  # archivo dañado o que no es .xlsx
        raise HTTPException(status_code=400, detail="No se pudo leer el archivo. Súbelo en formato Excel (.xlsx).") from error
    hoja = libro.worksheets[0]
    filas = hoja.iter_rows(values_only=True)
    encabezado = [normalizar(c or "") for c in next(filas, [])]
    indices: dict[str, int] = {}
    for campo, frase in COLUMNAS.items():
        for i, titulo in enumerate(encabezado):
            if frase in titulo and i not in indices.values():
                indices[campo] = i
                break
    faltan = [COLUMNAS[c] for c in OBLIGATORIAS if c not in indices]
    if faltan:
        raise HTTPException(status_code=400, detail="Al archivo le faltan columnas del formulario: " + ", ".join(faltan))
    salida = []
    for n, valores in enumerate(filas, start=2):
        if not any(v not in (None, "") for v in valores):
            continue
        salida.append({"fila": n, **{c: (valores[i] if i < len(valores) else None) for c, i in indices.items()}})
        if len(salida) > MAX_FILAS:
            raise HTTPException(status_code=400, detail=f"El archivo tiene más de {MAX_FILAS} filas")
    libro.close()
    return salida


def _ods_de(texto: str, catalogo: list[Ods]) -> list[int]:
    t = normalizar(texto)
    ids = {o.id for o in catalogo if normalizar(o.nombre) in t}
    ids |= {int(n) for n in re.findall(r"\bods\s*(\d{1,2})\b", t) if 1 <= int(n) <= 17}
    return sorted(ids)


def _misma_persona(a: str, b: str) -> bool:
    return normalizar(a) == normalizar(b)


def _nombre_del_correo(email: str, personas: list[str]) -> str:
    """De las personas del proyecto, la que más probablemente es dueña del correo (por sus apellidos)."""
    usuario = normalizar(email.split("@")[0])
    for persona in personas:
        apellidos = [p for p in normalizar(persona).split()[1:] if len(p) >= 4]
        if any(a in usuario for a in apellidos):
            return persona
    return personas[0] if personas else ""


def fila_desde_excel(datos: dict, catalogo_ods: list[Ods]) -> FilaLote:
    """Convierte una fila del Excel aplicando las reglas de la carga (se avisan en `avisos`)."""
    avisos: list[str] = []
    errores: list[str] = []
    lider = _texto(datos.get("lider"))
    equipo = _lista(datos.get("coautores"))
    if lider and any(_misma_persona(lider, p) for p in equipo):
        equipo = [p for p in equipo if not _misma_persona(lider, p)]
        avisos.append("Se quitó al líder de la lista de coautores")

    estado_txt = normalizar(_texto(datos.get("estado"))).replace("en ", "", 1)
    estado = ESTADOS.get(estado_txt)
    if estado is None:
        errores.append(f"Estado desconocido: «{_texto(datos.get('estado'))}»")
        estado = Estado.IDEA

    avance = _entero(datos.get("avance"))
    avance = 0 if avance is None else max(0, min(100, avance))
    if estado in RANGO_AVANCE:
        minimo, maximo, sugerido = RANGO_AVANCE[estado]
        if not minimo <= avance <= maximo:
            avisos.append(f"Avance ajustado de {avance} % a {sugerido} % por el estado «{NOMBRE_ESTADO[estado]}»")
            avance = sugerido

    area = _texto(datos.get("area"))
    ods = _ods_de(_texto(datos.get("ods")), catalogo_ods)
    if normalizar(area) == AREA_EDUCACION and ODS_EDUCACION not in ods:
        ods = sorted({*ods, ODS_EDUCACION})
        avisos.append("Se agregó el ODS 4 «Educación de calidad» (proyecto del área Educación)")

    email = _texto(datos.get("correo")).lower()
    return FilaLote(
        fila=datos["fila"],
        correo=email,
        nombre_cuenta=_nombre_del_correo(email, [lider, *equipo]),
        titulo=_texto(datos.get("titulo")),
        resumen=_texto(datos.get("resumen")),
        descripcion=_texto(datos.get("descripcion")),
        necesidades=_texto(datos.get("necesidades")),
        area=area,
        estado=estado,
        avance=avance,
        presupuesto=max(0, _entero(datos.get("presupuesto")) or 0),
        lider=lider,
        equipo=equipo,
        etiquetas=_lista(datos.get("etiquetas")),
        fecha_inicio=_fecha(datos.get("fecha_inicio")),
        fecha_fin=_fecha(datos.get("fecha_fin")),
        ods=ods,
        errores=errores,
        avisos=avisos,
    )


# ---- Validación -------------------------------------------------------------------------------

def _area(db: Session, nombre: str) -> Area | None:
    objetivo = normalizar(nombre)
    return next((a for a in db.scalars(select(Area)) if normalizar(a.nombre) == objetivo), None)


def revisar(db: Session, filas: list[FilaLote]) -> list[FilaLote]:
    """Vuelve a validar todas las filas contra la base y entre sí. No guarda nada."""
    titulos_en_base = {normalizar(t) for t in db.scalars(select(Proyecto.titulo))}
    ids_ods = set(db.scalars(select(Ods.id)))
    vistos: dict[str, int] = {}
    revisadas = []
    for f in filas:
        # Se conservan los errores de lectura (p. ej. estado desconocido) y se recalcula el resto.
        errores = [e for e in f.errores if e.startswith("Estado desconocido")]
        f.cuenta = ""
        if not f.incluir:
            f.errores = errores
            revisadas.append(f)
            continue
        try:
            f.correo = validar_correo(f.correo.strip().lower())
        except HTTPException as error:
            errores.append(f"Correo: {error.detail}")
        else:
            usuario = db.scalar(select(Usuario).where(func.lower(Usuario.email) == f.correo))
            if usuario is None:
                f.cuenta = "nueva"
                if not ajustes_srv.dominio_permitido(db, f.correo, Rol.ESTUDIANTE):
                    errores.append("El correo no es institucional")
                if not f.nombre_cuenta.strip():
                    errores.append("Falta el nombre de la cuenta")
            elif not usuario.activo:
                errores.append("Ya existe una cuenta con ese correo, pero está desactivada")
            else:
                f.cuenta = "existente"
                f.nombre_cuenta = usuario.nombre
        if not 5 <= len(f.titulo.strip()) <= 200:
            errores.append("El título debe tener entre 5 y 200 caracteres")
        else:
            clave = normalizar(f.titulo)
            if clave in titulos_en_base:
                errores.append("Ya hay un proyecto con ese título en Proyecta")
            elif clave in vistos:
                errores.append(f"El título se repite en la fila {vistos[clave]}")
            else:
                vistos[clave] = f.fila
        if len(f.resumen.strip()) < 10:
            errores.append("El resumen debe tener al menos 10 caracteres")
        elif len(f.resumen.strip()) > RESUMEN_MAX:
            errores.append(f"El resumen tiene {len(f.resumen.strip())} caracteres (máximo {RESUMEN_MAX})")
        area = _area(db, f.area)
        if area is None:
            errores.append(f"El área «{f.area}» no existe (créala en Administración → Catálogos)")
        else:
            f.area = area.nombre
        if not f.ods:
            errores.append("Falta al menos un ODS")
        elif not set(f.ods) <= ids_ods:
            errores.append("Algún ODS no existe")
        if len(f.lider) > 150:
            errores.append("El nombre del líder es muy largo (máximo 150 caracteres)")
        inicio = f.fecha_inicio or date.today()
        if f.fecha_fin and f.fecha_fin < inicio:
            errores.append("La fecha de cierre es anterior a la de inicio")
        f.errores = errores
        revisadas.append(f)
    return revisadas


# ---- Rutas ------------------------------------------------------------------------------------

@router.post("/previa", response_model=list[FilaLote])
async def vista_previa(db: DbSession, archivo: UploadFile = File(...)):
    """Lee el Excel y devuelve las filas listas para revisar. No guarda nada."""
    contenido = await archivo.read(MAX_BYTES + 1)
    if len(contenido) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="El archivo pesa más de 5 MB")
    catalogo_ods = list(db.scalars(select(Ods)))
    filas = [fila_desde_excel(d, catalogo_ods) for d in leer_excel(contenido)]
    if not filas:
        raise HTTPException(status_code=400, detail="El archivo no tiene respuestas")
    return revisar(db, filas)


@router.post("/revisar", response_model=list[FilaLote])
def revisar_filas(filas: list[FilaLote], db: DbSession):
    """Vuelve a validar las filas después de corregirlas en la vista previa."""
    return revisar(db, filas)


@router.post("/confirmar", response_model=ResultadoLote)
def confirmar(filas: list[FilaLote], admin: Admin, db: DbSession, tareas: BackgroundTasks):
    """Crea cuentas y proyectos. Si alguna fila incluida tiene errores, no se guarda nada."""
    filas = revisar(db, filas)
    incluidas = [f for f in filas if f.incluir]
    if not incluidas:
        raise HTTPException(status_code=400, detail="No hay filas para cargar")
    con_error = [f.fila for f in incluidas if f.errores]
    if con_error:
        raise HTTPException(status_code=422, detail="Corrige o excluye las filas con problemas: " + ", ".join(map(str, con_error)))

    from app.modules.experiencia.servicio import sumar
    from app.modules.insignias.servicio import evaluar_ids

    settings = get_settings()
    por_correo: dict[str, list[FilaLote]] = defaultdict(list)
    for f in incluidas:
        por_correo[f.correo].append(f)

    nuevas: list[Usuario] = []
    existentes: list[Usuario] = []
    titulos: dict[uuid.UUID, list[str]] = {}
    with silencio():
        for email, grupo in por_correo.items():
            usuario = db.scalar(select(Usuario).where(func.lower(Usuario.email) == email))
            if usuario is None:
                usuario = Usuario(email=email, nombre=grupo[0].nombre_cuenta.strip()[:150], rol=Rol.ESTUDIANTE.value,
                                  hashed_password=hash_password(secrets.token_urlsafe(32)), habilidades=[],
                                  intereses=[], verificado=True, activo=True)
                db.add(usuario)
                db.flush()
                nuevas.append(usuario)
            else:
                existentes.append(usuario)
            titulos[usuario.id] = []
            for f in grupo:
                proyecto = Proyecto(
                    titulo=f.titulo.strip(), resumen=f.resumen.strip(), descripcion=f.descripcion,
                    necesidades=f.necesidades, estado=f.estado, avance=f.avance, presupuesto=f.presupuesto,
                    lider=f.lider.strip() or usuario.nombre, equipo=f.equipo, etiquetas=f.etiquetas,
                    fecha_inicio=f.fecha_inicio or date.today(), fecha_fin=f.fecha_fin, creado_por_id=usuario.id,
                )
                proyecto.area = _area(db, f.area)
                proyecto.ods = list(db.scalars(select(Ods).where(Ods.id.in_(f.ods))))
                db.add(proyecto)
                db.flush()
                sumar(db, usuario, "proyecto_registrado", str(proyecto.id), f"Registró «{proyecto.titulo}»")
                titulos[usuario.id].append(proyecto.titulo)
            evaluar_ids(db, [usuario.id])
        registrar(db, admin, "proyectos.lote", f"{len(incluidas)} proyectos",
                  f"Cuentas nuevas: {len(nuevas)}. Cuentas existentes: {len(existentes)}.")
        db.commit()

    # Un solo correo por persona, después de guardar todo.
    base = settings.frontend_url.rstrip("/")
    dias = settings.lote_enlace_dias
    for usuario in nuevas:
        token = create_token(str(usuario.id), "restablecer", dias * 24 * 60, huella=huella_password(usuario.hashed_password))
        tareas.add_task(correo.enviar, correo.cuenta_creada_lote(
            usuario.email, usuario.nombre, f"{base}/restablecer?token={token}", dias, titulos[usuario.id]))
    for usuario in existentes:
        tareas.add_task(correo.enviar, correo.proyecto_registrado_lote(
            usuario.email, usuario.nombre, f"{base}/perfil", titulos[usuario.id]))
    return ResultadoLote(proyectos=len(incluidas), cuentas_nuevas=len(nuevas), cuentas_existentes=len(existentes),
                         correos=len(nuevas) + len(existentes))
