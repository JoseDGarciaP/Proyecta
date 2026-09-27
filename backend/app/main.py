from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.actores.router import router as actores
from app.modules.alianzas.router import router as alianzas
from app.modules.auth.router import router as auth
from app.modules.catalogo.router import router as catalogo
from app.modules.ia.router import router as ia
from app.modules.oportunidades.router import router as oportunidades
from app.modules.perfil.router import router as perfil
from app.modules.proyectos.router import router as proyectos
from app.modules.usuarios.router import router as usuarios

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, usuarios, perfil, catalogo, proyectos, alianzas, actores, oportunidades, ia):
    app.include_router(r)


@app.get("/api/salud", tags=["sistema"])
def salud():
    return {"estado": "ok"}
