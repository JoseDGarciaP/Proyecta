# Proyecta

Plataforma para **centralizar proyectos e iniciativas** y facilitar su articulación con actores
y oportunidades de apoyo. Este repositorio contiene una base funcional: panel de métricas,
registro y consulta de proyectos, directorio de actores, cartelera de oportunidades y un
asistente de IA que resume proyectos y sugiere convocatorias afines.

> Estado: maqueta funcional navegable. Arranca sin backend (datos de ejemplo en memoria) y se
> conecta a Supabase en cuanto se definen las variables de entorno.

## Stack

| Capa | Tecnología | Versión |
|------|-----------|---------|
| UI | React + React Router | 19.3 · 7.18 |
| Build | Vite (rolldown) | 8.3 |
| Lenguaje | TypeScript | 5.9 |
| Estilos | Tailwind CSS (config CSS-first) | 4.3 |
| Gráficas | Recharts | 3.10 |
| Íconos | lucide-react | 1.46 |
| Datos | Supabase JS | 2.116 |
| IA | Python · FastAPI | 3.11+ · 0.141 |

Todas las versiones fijadas reportan `0 vulnerabilities` en `npm audit` al momento de la
generación del proyecto.

## Puesta en marcha

```bash
npm install
cp .env.example .env     # opcional: sin variables arranca en modo demostración
npm run dev              # http://localhost:5173
```

Otros comandos: `npm run build` (producción), `npm run preview`, `npm run typecheck`.

### Conectar Supabase

1. Crea un proyecto en [supabase.com](https://supabase.com).
2. Ejecuta `supabase/schema.sql` en el editor SQL (crea tablas, índices, vista de métricas y
   políticas RLS). Opcionalmente `supabase/seed.sql` para datos de prueba.
3. Copia la URL y la *anon key* del proyecto en `.env`:

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=...
```

La app detecta las credenciales sola: si existen consulta la base de datos, si no usa los datos
de ejemplo. Toda la conmutación vive en `src/lib/api.ts`, así que las vistas no cambian.

### Servicio de IA

```bash
cd ai
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Luego define `VITE_AI_API_URL=http://localhost:8000` en el `.env` del frontend. Sin API key el
servicio responde con una heurística local y marca el resultado como simulado. Detalles en
[`ai/README.md`](ai/README.md).

## Estructura

```
src/
  components/   Layout, tarjetas, gráficas, panel de IA, primitivas de UI
  pages/        Panel, Proyectos, Detalle, Registro, Actores, Oportunidades
  lib/          api.ts (capa de datos), supabase.ts, ai.ts, types.ts, chartTheme.ts
  hooks/        useDatos, useTheme
  data/         datos de ejemplo del modo demostración
supabase/       schema.sql (tablas + RLS) y seed.sql
ai/             servicio FastAPI de resúmenes y recomendaciones
```

## Decisiones de diseño

- **Una sola capa de datos.** `src/lib/api.ts` decide entre Supabase y datos locales; ninguna
  vista sabe de dónde vienen los registros.
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
- **RLS activo desde el inicio.** Lectura pública del catálogo; creación y edición solo para
  usuarios autenticados y sobre sus propios registros.
- **La IA nunca bloquea la demostración.** Si el servicio no está disponible, el frontend cae a
  una heurística local y lo advierte en pantalla.

## Siguientes pasos sugeridos

- Autenticación de usuarios (Supabase Auth) y roles por facultad o programa.
- Gestión de la relación proyecto–actor desde la interfaz (tabla `proyecto_actores`).
- Búsqueda semántica de proyectos con `pgvector` y embeddings.
- Carga de anexos con Supabase Storage y control de versiones documentales.
