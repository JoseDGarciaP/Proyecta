#!/usr/bin/env sh
# Trae la última versión de main y reconstruye. Las migraciones se aplican solas al arrancar la API.
set -eu
cd "$(dirname "$0")/.."
git pull --ff-only origin main
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion up -d --build
docker image prune -f
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion ps
