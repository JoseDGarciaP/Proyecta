-- =====================================================================
-- Proyecta — esquema base
-- Ejecutar en el editor SQL de Supabase (o con la CLI: supabase db push)
-- =====================================================================

create extension if not exists "pgcrypto";

-- Tipos ---------------------------------------------------------------
do $$ begin
  create type estado_proyecto as enum ('idea','formulacion','ejecucion','finalizado','pausado');
exception when duplicate_object then null; end $$;

do $$ begin
  create type tipo_actor as enum ('universidad','empresa','estado','comunidad','ong');
exception when duplicate_object then null; end $$;

do $$ begin
  create type tipo_oportunidad as enum ('convocatoria','financiacion','mentoria','infraestructura');
exception when duplicate_object then null; end $$;

-- Tablas --------------------------------------------------------------
create table if not exists public.actores (
  id         uuid primary key default gen_random_uuid(),
  nombre     text        not null,
  tipo       tipo_actor  not null,
  sector     text        not null default '',
  contacto   text        not null default '',
  creado_en  date        not null default current_date
);

create table if not exists public.proyectos (
  id           uuid primary key default gen_random_uuid(),
  titulo       text            not null,
  resumen      text            not null default '',
  descripcion  text            not null default '',
  area         text            not null,
  estado       estado_proyecto not null default 'idea',
  avance       smallint        not null default 0 check (avance between 0 and 100),
  presupuesto  bigint          not null default 0 check (presupuesto >= 0),
  lider        text            not null default '',
  equipo       text[]          not null default '{}',
  etiquetas    text[]          not null default '{}',
  fecha_inicio date            not null default current_date,
  fecha_fin    date,
  creado_por   uuid references auth.users (id) on delete set null,
  creado_en    date            not null default current_date,
  constraint fechas_coherentes check (fecha_fin is null or fecha_fin >= fecha_inicio)
);

create table if not exists public.proyecto_actores (
  proyecto_id uuid not null references public.proyectos (id) on delete cascade,
  actor_id    uuid not null references public.actores  (id) on delete cascade,
  rol         text not null default 'aliado',
  primary key (proyecto_id, actor_id)
);

create table if not exists public.oportunidades (
  id        uuid primary key default gen_random_uuid(),
  titulo    text             not null,
  entidad   text             not null default '',
  tipo      tipo_oportunidad not null,
  monto     bigint,
  cierra_en date             not null,
  areas     text[]           not null default '{}',
  url       text             not null default ''
);

-- Índices -------------------------------------------------------------
create index if not exists proyectos_estado_idx  on public.proyectos (estado);
create index if not exists proyectos_area_idx    on public.proyectos (area);
create index if not exists proyectos_creado_idx  on public.proyectos (creado_en desc);
create index if not exists proyectos_texto_idx
  on public.proyectos using gin (to_tsvector('spanish', titulo || ' ' || resumen || ' ' || descripcion));
create index if not exists oportunidades_cierre_idx on public.oportunidades (cierra_en);

-- Vista de métricas para el panel -------------------------------------
create or replace view public.metricas_resumen as
select
  count(*)                                             as total,
  count(*) filter (where estado = 'ejecucion')         as en_ejecucion,
  coalesce(sum(presupuesto), 0)                        as presupuesto_total,
  coalesce(round(avg(avance)), 0)                      as avance_promedio
from public.proyectos;

-- Seguridad a nivel de fila -------------------------------------------
alter table public.proyectos        enable row level security;
alter table public.actores          enable row level security;
alter table public.oportunidades    enable row level security;
alter table public.proyecto_actores enable row level security;

-- Lectura pública (catálogo abierto). Ajustar si la plataforma se vuelve privada.
drop policy if exists "lectura publica proyectos" on public.proyectos;
create policy "lectura publica proyectos" on public.proyectos for select using (true);

drop policy if exists "lectura publica actores" on public.actores;
create policy "lectura publica actores" on public.actores for select using (true);

drop policy if exists "lectura publica oportunidades" on public.oportunidades;
create policy "lectura publica oportunidades" on public.oportunidades for select using (true);

drop policy if exists "lectura publica relaciones" on public.proyecto_actores;
create policy "lectura publica relaciones" on public.proyecto_actores for select using (true);

-- Escritura solo para usuarios autenticados; edición solo del autor.
drop policy if exists "crear proyectos autenticado" on public.proyectos;
create policy "crear proyectos autenticado" on public.proyectos
  for insert to authenticated with check (auth.uid() = creado_por or creado_por is null);

drop policy if exists "editar proyectos propios" on public.proyectos;
create policy "editar proyectos propios" on public.proyectos
  for update to authenticated using (auth.uid() = creado_por) with check (auth.uid() = creado_por);

drop policy if exists "eliminar proyectos propios" on public.proyectos;
create policy "eliminar proyectos propios" on public.proyectos
  for delete to authenticated using (auth.uid() = creado_por);
