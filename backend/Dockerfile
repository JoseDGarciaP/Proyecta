# API de Proyecta para producción (sirve en x86_64 y en ARM, como la VM gratuita de Oracle).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # El modelo de similitud se descarga aquí la primera vez; el volumen lo conserva entre reinicios.
    HF_HOME=/cache/huggingface

WORKDIR /app

# Con CON_EMBEDDINGS=false (servidores de 512 MB, como el plan gratuito de Render) no se instala
# PyTorch ni sentence-transformers: la similitud usa palabras en común.
ARG CON_EMBEDDINGS=true

# PyTorch solo CPU (~200 MB). Desde PyPI en x86_64 traería las librerías de CUDA (varios GB).
RUN if [ "$CON_EMBEDDINGS" = "true" ]; then pip install torch --index-url https://download.pytorch.org/whl/cpu; fi

COPY requirements.txt .
RUN if [ "$CON_EMBEDDINGS" = "true" ]; then pip install -r requirements.txt; \
    else grep -v '^sentence-transformers' requirements.txt > /tmp/req.txt && pip install -r /tmp/req.txt; fi

COPY . .

# /archivos guarda los certificados y evidencias que sube la gente (volumen «archivos» en producción).
RUN useradd --create-home proyecta && mkdir -p /cache /archivos && chown proyecta /cache /archivos
USER proyecta

EXPOSE 8000
# Aplica las migraciones pendientes y arranca. Un solo proceso: el modelo de similitud ocupa ~1 GB de RAM.
# PORT lo define el servidor si hace falta (Render); por defecto 8000.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
