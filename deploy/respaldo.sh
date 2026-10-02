#!/usr/bin/env sh
# Copia de seguridad diaria de la base. Programar con:  crontab -e  →
#   30 3 * * * sh /home/ubuntu/Proyecta/deploy/respaldo.sh >> /home/ubuntu/respaldos/registro.log 2>&1
# Guarda los últimos 14 días en ~/respaldos.
set -eu
cd "$(dirname "$0")/.."
destino="$HOME/respaldos"
mkdir -p "$destino"
archivo="$destino/proyecta-$(date +%Y%m%d-%H%M).sql.gz"
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec -T db \
  pg_dump -U proyecta -d proyecta --no-owner | gzip > "$archivo"
find "$destino" -name 'proyecta-*.sql.gz' -mtime +14 -delete
echo "$(date -Iseconds) respaldo listo: $archivo"
