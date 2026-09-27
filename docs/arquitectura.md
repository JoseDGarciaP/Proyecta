# Arquitectura de Proyecta

## 1. Decisiones principales

| Tema | Decisión | Por qué |
|---|---|---|
| Estilo | **Monolito modular**: una interfaz React y una API FastAPI | Equipo de 3 personas y un semestre. Cada módulo vive en su carpeta, así que se puede separar después si hiciera falta. |
| Backend | **Solo FastAPI** (sin Node.js) | La IA es Python; un segundo backend duplicaría la lógica y la autenticación. |
| Acceso a datos | La interfaz nunca habla directo con la base; todo pasa por la API | Permisos, validaciones e IA en un solo lugar y probados con pytest. |
| Base de datos | **Una PostgreSQL** con pgvector: Supabase en producción, Docker en local | Supabase ya es PostgreSQL; no son dos bases. pgvector guardará los embeddings junto a los datos. |
| Esquema | SQLAlchemy 2 + Alembic | Las migraciones quedan versionadas en el repositorio. |
| Autenticación | JWT propio con contraseña cifrada (bcrypt). Correo `@ufpso.edu.co` obligatorio salvo para aliados externos | Simple y bajo control del equipo. |
| Búsqueda semántica (pendiente) | sentence-transformers + pgvector, sin LlamaIndex | pgvector ya resuelve la similitud; LlamaIndex agrega una capa sin necesidad para este alcance. |
| LLM | **Ollama local y gratuito** (`llama3.2:3b`) por defecto; Claude opcional con `IA_PROVEEDOR=anthropic`; reglas locales si no hay modelo | El equipo quiere un modelo gratuito, y la plataforma funciona igual sin modelo. |
| Oportunidades | Las carga un administrador | Garantiza datos desde el día uno. Importarlas de Minciencias/SENA queda como mejora. |

## 2. Vista general

```
Navegador (React + TypeScript)
   src/lib/api.ts ── sin VITE_API_URL ──> datos de ejemplo (modo demostración)
        │ HTTP/JSON + token JWT
        ▼
FastAPI (backend/app)
 ├─ auth            registro e ingreso
 ├─ usuarios        perfil, habilidades, intereses
 ├─ catalogo        áreas y 17 ODS
 ├─ proyectos       registro, filtros, permisos de autor
 ├─ actores         organizaciones aliadas y su vínculo con proyectos
 ├─ oportunidades   convocatorias, fondos, mentorías, infraestructura
 └─ ia              resumen y recomendación explicable ── Ollama local (o Claude)
        │
        ▼
PostgreSQL (+ pgvector)
```

## 3. Cómo agregar un módulo

1. Crear `backend/app/modules/<nombre>/` con `models.py`, `schemas.py` y `router.py`.
2. Importar el modelo en `backend/app/models.py` y registrar el router en `backend/app/main.py`.
3. Generar la migración: `alembic revision --autogenerate -m "..."` y revisarla.
4. Escribir sus pruebas en `backend/tests/`.
5. En la interfaz, agregar las funciones en `src/lib/api.ts` y los tipos en `src/lib/types.ts`.

La API responde con los mismos nombres de campo que `src/lib/types.ts`, así que las vistas no
cambian al pasar de los datos de ejemplo a la base real.

## 4. Modelo de datos

- **usuarios**: email, contraseña cifrada, nombre, rol (`estudiante`, `docente`, `administrativo`, `aliado`, `admin`), programa, bio, habilidades, intereses.
- **areas** (Tecnología, Ambiente, Salud, Educación, Agroindustria, Social, Energía) y **ods** (1 a 17): catálogos cargados por la migración inicial.
- **proyectos**: título, resumen, descripción, necesidades, área, estado (`idea`, `formulacion`, `ejecucion`, `finalizado`, `pausado`), avance, presupuesto, líder, equipo, etiquetas, fechas, autor; ODS (muchos a muchos) y actores (`proyecto_actores`, con rol).
- **actores**: nombre, tipo (`universidad`, `empresa`, `estado`, `comunidad`, `ong`), sector, contacto.
- **oportunidades**: título, entidad, tipo, descripción, monto, fecha de cierre, URL; áreas y ODS (muchos a muchos).

## 5. Endpoints

| Método | Ruta | Acceso |
|---|---|---|
| POST | `/api/auth/registro`, `/api/auth/login` | público |
| GET/PATCH | `/api/usuarios/yo` | con sesión |
| GET | `/api/usuarios`, `/api/usuarios/{id}` | con sesión |
| GET | `/api/catalogo/areas`, `/api/catalogo/ods` | público |
| GET | `/api/proyectos` (filtros `q`, `area`, `estado`, `ods`), `/api/proyectos/{id}` | público |
| POST | `/api/proyectos` | con sesión |
| PATCH/DELETE | `/api/proyectos/{id}` | autor o admin |
| GET | `/api/actores`, `/api/oportunidades` (filtros `q`, `area`, `ods`, `tipo`, `abiertas`) | público |
| POST/PUT/DELETE | `/api/actores...`, `/api/oportunidades...` | admin |
| POST | `/api/ia/proyectos/{id}/analisis` | público |

Documentación interactiva en `http://localhost:8000/docs`.

## 6. Plan de sprints (2 semanas cada uno)

| Sprint | Objetivo | Estado |
|---|---|---|
| 0 | Requisitos, historias de usuario, diagramas, tablero en Trello | pendiente (documentación) |
| 1 | Interfaz base, autenticación, catálogo de áreas y ODS | **hecho** |
| 2 | Proyectos: registro, explorador, detalle; falta edición y vínculo de actores en la interfaz | **en curso** |
| 3 | Pantallas de administrador para actores y oportunidades; datos reales de convocatorias | pendiente |
| 4 | IA: embeddings, recomendación de colaboradores, búsqueda en lenguaje natural | pendiente (ya hay recomendación por reglas) |
| 5 | Alianzas (solicitar unirse, aceptar/rechazar, historial) y notificaciones | pendiente |
| 6 | Estadísticas, auditoría, despliegue (API en Render/Railway, base en Supabase, interfaz en Vercel), pruebas con usuarios | pendiente |

## 7. Pendientes de definir con el equipo

- Qué significa "tasa de éxito" para el panel de estadísticas.
- Cómo se verifica a un aliado externo (hoy se registra con cualquier correo).
- Aviso de privacidad y autorización de tratamiento de datos (Ley 1581 de 2012) en el registro.
- Dónde se despliega y qué modelo de lenguaje se usa.
