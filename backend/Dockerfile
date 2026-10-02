# API de Proyecta para producción (sirve en x86_64 y en ARM, como la VM gratuita de Oracle).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # El modelo de similitud se descarga aquí la primera vez; el volumen lo conserva entre reinicios.
    HF_HOME=/cache/huggingface

WORKDIR /app

# PyTorch solo CPU (~200 MB). Desde PyPI en x86_64 traería las librerías de CUDA (varios GB).
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home proyecta && mkdir -p /cache && chown proyecta /cache
USER proyecta

EXPOSE 8000
# Aplica las migraciones pendientes y arranca. Un solo proceso: el modelo de similitud ocupa ~1 GB de RAM.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
