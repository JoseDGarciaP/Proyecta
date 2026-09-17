from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import RespuestaAnalisis, SolicitudAnalisis
from .servicio import analizar

load_dotenv()

app = FastAPI(
    title="Proyecta · servicio de IA",
    version="0.1.0",
    description="Resúmenes ejecutivos y recomendación de oportunidades para los proyectos registrados.",
)

origenes = [o.strip() for o in os.getenv("ORIGENES_PERMITIDOS", "http://localhost:5173").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/salud")
async def salud() -> dict[str, object]:
    return {"estado": "ok", "modelo_configurado": bool(os.getenv("ANTHROPIC_API_KEY"))}


@app.post("/analizar", response_model=RespuestaAnalisis)
async def analizar_proyecto(solicitud: SolicitudAnalisis) -> RespuestaAnalisis:
    return await analizar(solicitud.proyecto, solicitud.oportunidades)
