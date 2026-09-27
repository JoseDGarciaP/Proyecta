# Proyecta

Plataforma para **centralizar proyectos e iniciativas** y facilitar su articulación con actores
y oportunidades de apoyo. Este repositorio contiene una base funcional: panel de métricas,
registro y consulta de proyectos, directorio de actores, cartelera de oportunidades y un
asistente de IA que resume proyectos y sugiere convocatorias afines.

> Estado: interfaz navegable conectada a una API en FastAPI con login, roles y base de datos
> PostgreSQL. Sin backend configurado arranca en modo demostración con datos de ejemplo.

## Stack

| Capa | Tecnología | Versión |
|------|-----------|---------|
| UI | React + React Router | 19.3 · 7.18 |
| Build | Vite (rolldown) | 8.3 |
| Lenguaje | TypeScript | 5.9 |
| Estilos | Tailwind CSS (config CSS-first) | 4.3 |
| Gráficas | Recharts | 3.10 |
| Íconos | lucide-react | 1.46 |
| API | Python · FastAPI · SQLAlchemy · Alembic | 3.11+ · 0.141 · 2.1 · 1.20 |
| Base de datos | PostgreSQL (Supabase en producción, Docker en local) | 16 |

La arquitectura completa, el modelo de datos y el plan de sprints están en
[`docs/arquitectura.md`](docs/arquitectura.md).

## Puesta en marcha

### Solo la interfaz (modo demostración)

```bash
npm install
npm run dev              # http://localhost:5173
```

Sin `VITE_API_URL` la app usa los datos de `src/data/mock.ts` en memoria.
Otros comandos: `npm run build` (producción), `npm run preview`, `npm run typecheck`.

### Con backend y base de datos

```bash
docker compose up -d db                 # PostgreSQL + pgvector local (o usa la URL de Supabase)

cd backend
python -m venv .venv
source .venv/bin/activate               # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                    # ajusta DATABASE_URL y SECRET_KEY
alembic upgrade head                    # crea las tablas y carga áreas y ODS
python -m scripts.seed_demo             # opcional: los mismos datos de ejemplo de la maqueta
python -m scripts.create_admin admin@ufpso.edu.co "Nombre Admin"
fastapi dev app/main.py                 # http://localhost:8000/docs
pytest                                  # pruebas (SQLite en memoria, no tocan tu base)
```

Luego, en la raíz, crea `.env` con `VITE_API_URL=http://localhost:8000` y ejecuta `npm run dev`.

### Asistente de IA

El análisis de proyectos vive en el backend (`backend/app/modules/ia`). Sin `ANTHROPIC_API_KEY` el
resumen sale de reglas locales y se marca como simulado; las recomendaciones de oportunidades
siempre se calculan en el backend y explican por qué se sugieren (área 0.5, ODS en común 0.2,
etiquetas 0.15, vigencia 0.15; solo oportunidades abiertas).

## Estructura

```
src/
  components/   Layout, tarjetas, gráficas, panel de IA, RequiereSesion, primitivas de UI
  pages/        Panel, Proyectos, Detalle, Registro de proyecto, Actores, Oportunidades, Ingresar, Registro
  lib/          api.ts (capa de datos), http.ts (cliente de la API), sesion.tsx, ai.ts, types.ts, chartTheme.ts
  hooks/        useDatos, useTheme
  data/         datos de ejemplo del modo demostración
backend/
  app/core/     configuración, base de datos, seguridad (JWT), dependencias
  app/modules/  auth, usuarios, catalogo (áreas y ODS), proyectos, actores, oportunidades, ia
  alembic/      migraciones
  scripts/      create_admin, seed_demo
  tests/        pytest
docs/           arquitectura y plan de sprints
```

## Decisiones de diseño

- **Una sola capa de datos.** `src/lib/api.ts` decide entre la API y datos locales; ninguna
  vista sabe de dónde vienen los registros.
- **Un solo backend.** FastAPI concentra datos, permisos e IA; la API responde con los mismos
  nombres de campo que `src/lib/types.ts`.
- **Identidad azul + fucsia.** Las dos escalas viven como tokens en `src/index.css`
  (`--color-brand-*` azul, `--color-accent-*` fucsia); botones, logo y barras de avance usan el
  degradado entre ambas. Cambiar la marca es editar esas dos escalas.
- **Paleta de visualización validada.** La serie doble del panel usa la pareja azul + fucsia
  (`DUO_LIGHT` / `DUO_DARK`), verificada en ambos modos: separación ΔE 27 con visión normal y
  ΔE >= 13 simulando daltonismo, con contraste >= 3:1 contra la tarjeta. El donut de estados
  conserva ocho tonos categóricos en orden fijo, porque ahí lo que manda es poder distinguir
  cinco categorías a la vez (`src/lib/chartTheme.ts`).
- **Modo claro y oscuro.** Toma la preferencia del sistema en la primera visita, se puede
  alternar desde la barra superior y la elección queda guardada (`src/hooks/useTheme.ts`).
- **Permisos en la API.** Lectura pública del catálogo; crear proyectos requiere sesión y solo
  quien lo registró (o un admin) lo edita. Actores y oportunidades los gestiona un admin.
- **La IA nunca bloquea la demostración.** Si la API no está disponible, el frontend cae a
  una heurística local y lo advierte en pantalla.

## Siguientes pasos sugeridos

- Pantallas de administración para cargar actores y oportunidades (hoy solo por la API).
- Editar proyectos y vincular actores desde la interfaz (la API ya lo permite).
- Perfiles con habilidades e intereses en la interfaz, para recomendar colaboradores.
- Búsqueda semántica y recomendación con embeddings (`pgvector`).
- Solicitudes de alianza y notificaciones.
