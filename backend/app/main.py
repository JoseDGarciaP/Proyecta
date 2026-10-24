import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.deps import get_current_user, requiere, requiere_panel
from app.modules.actores.router import router as actores
from app.modules.admin.router import routers as admin
from app.modules.alianzas.router import router as alianzas
from app.modules.auth.router import router as auth
from app.modules.catalogo.router import router as catalogo
from app.modules.chat.router import router as chat
from app.modules.ia.router import router as ia
from app.modules.evidencias import router as evidencias
from app.modules.experiencia import router as experiencia
from app.modules.insignias import router as insignias
from app.modules.postulaciones import router as postulaciones
from app.modules.notificaciones.router import router as notificaciones
from app.modules.insignias.servicio import tarea_periodica as tarea_insignias
from app.modules.notificaciones.servicio import tarea_resumenes
from app.modules.oportunidades.router import router as oportunidades
from app.modules.parametros.router import router as parametros
from app.modules.perfil.router import router as perfil
from app.modules.publico.router import router as publico
from app.modules.proyectos.router import router as proyectos
from app.modules.roles import router as roles
from app.modules.usuarios.router import router as usuarios

settings = get_settings()


async def _ciclo(minutos: int, tarea) -> None:
    """Corre `tarea` cada `minutos` (resumen de mensajes sin leer, revisión de insignias)."""
    while True:
        await asyncio.sleep(minutos * 60)
        await run_in_threadpool(tarea)


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    tareas = [
        asyncio.create_task(_ciclo(settings.resumen_intervalo_minutos, tarea_resumenes)),
        asyncio.create_task(_ciclo(settings.insignias_intervalo_minutos, tarea_insignias)),
    ] if settings.resumen_automatico else []
    yield
    for tarea in tareas:
        tarea.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await tarea


app = FastAPI(title=settings.app_name, version="0.4.0", lifespan=ciclo_de_vida)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Público: ingreso/registro, catálogos (los usa el formulario de registro) y cifras de la página de inicio.
for r in (auth, catalogo, publico, roles.publico):
    app.include_router(r)

# Todo lo demás exige una sesión de un usuario con el correo verificado.
for r in (usuarios, perfil, proyectos, alianzas, chat, actores, oportunidades, notificaciones, parametros,
          roles.lectura, insignias.router, experiencia.router, postulaciones.router, evidencias.router):
    app.include_router(r, dependencies=[Depends(get_current_user)])
app.include_router(ia, dependencies=[Depends(requiere("ia.usar"))])

# Panel de administración: cada sección exige su permiso (ver app.modules.roles.permisos).
for r in (*admin, roles.admin, insignias.admin, experiencia.admin, evidencias.admin):
    app.include_router(r, dependencies=[Depends(requiere_panel)])
# Las postulaciones las gestiona quien administra oportunidades (no necesita otra sección del panel).
app.include_router(postulaciones.admin, dependencies=[Depends(get_current_user)])


@app.get("/api/salud", tags=["sistema"])
def salud():
    return {"estado": "ok"}
