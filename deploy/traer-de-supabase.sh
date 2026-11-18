#!/usr/bin/env sh
# Copia UNA SOLA VEZ los datos que hay en Supabase a la base de la VM.
# Uso (en la VM, dentro de ~/Proyecta):
#   sh deploy/traer-de-supabase.sh "postgresql://postgres.xxxx:CLAVE@aws-0-xx.pooler.supabase.com:5432/postgres"
# La cadena es la del «Session pooler» de Supabase (Connect → Connection string → Session pooler, puerto 5432).
#
# Qué hace: la API crea las tablas con sus migraciones, se detiene, se vacían las tablas de la VM
# y se cargan los datos de Supabase. Los archivos subidos (certificados, evidencias) no están en la base:
# los que había en Render ya se perdieron con sus reinicios.
set -eu
cd "$(dirname "$0")/.."
ORIGEN="${1:?Pasa la cadena del Session pooler de Supabase entre comillas}"

dc() { docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion "$@"; }
local_psql() { dc exec -T db psql -U proyecta -d proyecta -v ON_ERROR_STOP=1 "$@"; }

echo "1/5 Encendiendo la base y la API para crear las tablas..."
dc up -d db api
i=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' "$(dc ps -q api)")" = "healthy" ]; do
  i=$((i + 1))
  if [ "$i" -gt 72 ]; then
    echo "La API no quedó lista en 6 minutos. Revisa:  docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion logs api"
    exit 1
  fi
  sleep 5
done
dc stop api

echo "2/5 Comparando la versión de las migraciones..."
v_origen=$(dc exec -T db psql "$ORIGEN" -Atc "SELECT version_num FROM public.alembic_version")
v_local=$(local_psql -Atc "SELECT version_num FROM alembic_version")
if [ "$v_origen" != "$v_local" ]; then
  echo "Supabase está en la migración $v_origen y la VM en $v_local."
  echo "Ambas deben ser iguales: despliega en Render (o en la VM) la misma versión de main y vuelve a intentar."
  dc up -d api
  exit 1
fi

echo "3/5 Descargando los datos de Supabase..."
volcado=$(mktemp)
dc exec -T db pg_dump "$ORIGEN" --data-only --schema=public \
  --exclude-table=public.alembic_version --no-owner --no-privileges > "$volcado"

echo "4/5 Cargando los datos en la VM (todo o nada)..."
{
  # Desactiva las llaves foráneas durante la carga para que el orden de las tablas no importe.
  echo "SET session_replication_role = replica;"
  echo "DO \$\$ DECLARE t record; BEGIN
          FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version' LOOP
            EXECUTE 'TRUNCATE TABLE public.' || quote_ident(t.tablename) || ' CASCADE';
          END LOOP;
        END \$\$;"
  cat "$volcado"
} | local_psql --single-transaction -q > /dev/null
rm -f "$volcado"

echo "5/5 Encendiendo todo..."
dc up -d
echo "Listo. Los datos de Supabase ya están en la VM."
