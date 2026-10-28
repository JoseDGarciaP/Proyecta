"""cierra las tablas a la API automática de Supabase (solo si la base es de Supabase)

Supabase publica el esquema public por su API REST: con la clave «anon», que viaja en cualquier
página, se podrían leer y cambiar las tablas que no tengan RLS. Proyecta no usa esa API (todo pasa
por FastAPI, que se conecta como postgres y no se ve afectada), así que se activa RLS sin políticas
y se quitan los permisos de los roles anon y authenticated, también para las tablas futuras.
En un PostgreSQL normal (sin esos roles) esta migración no hace nada.

Revision ID: 0011
Revises: 0010
"""
from typing import Sequence, Union

from alembic import op


revision: str = '0011'
down_revision: Union[str, None] = '0010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
DO $$
DECLARE
  t record;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
     OR NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    RETURN;
  END IF;
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t.tablename);
  END LOOP;
  REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
  REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM anon, authenticated;
END $$;
""")


def downgrade() -> None:
    # No se devuelven los permisos: abrir las tablas a la API pública nunca es lo que se busca.
    pass
