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

### Asistente de IA (gratuito con Ollama)

El análisis de proyectos vive en el backend (`backend/app/modules/ia`). Por defecto el resumen
lo redacta un modelo local y gratuito con [Ollama](https://ollama.com):

1. Instala Ollama desde <https://ollama.com/download> (Windows, macOS o Linux). Queda corriendo
   en segundo plano en `http://localhost:11434`.
2. Descarga el modelo una vez: `ollama pull llama3.2:3b` (unos 2 GB; funciona en CPU con 8 GB de RAM).
3. Reinicia la API. El primer análisis tarda más porque el modelo se carga en memoria.

Se cambia en `backend/.env`: `IA_PROVEEDOR=ollama` (por defecto), `anthropic` (Claude, requiere
`ANTHROPIC_API_KEY`) o `reglas` (sin modelo). Otro modelo de Ollama se elige con `OLLAMA_MODEL`
(por ejemplo `qwen2.5:3b` o, con más memoria, `llama3.1:8b`). Si el proveedor no responde, el
resumen sale de reglas locales y la interfaz lo marca como simulado.

Las recomendaciones de oportunidades no dependen del modelo: siempre las calcula el backend y
explican por qué se sugieren (área 0.5, ODS en común 0.2, etiquetas 0.15, vigencia 0.15; solo
oportunidades abiertas). Con embeddings, el puntaje final es 70 % reglas + 30 % similitud semántica.

### Similitud semántica (sentence-transformers, gratuito)

Todo lo relacionado con similitud usa [sentence-transformers](https://www.sbert.net) con el modelo
multilingüe `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensiones, corre en CPU) y guarda los
vectores en PostgreSQL con **pgvector** (módulo `backend/app/modules/similitud`):

| Función | Dónde se ve |
|---|---|
| Proyectos que buscan un perfil como el mío | Mi perfil → Sugerencias para ti |
| Oportunidades para mis proyectos | Mi perfil y Asistente de articulación |
| Proyectos similares (articularse o evitar duplicados) | Detalle del proyecto |
| Posibles colaboradores según «Lo que necesita» | Detalle del proyecto (solo su responsable) |
| Búsqueda por significado de convocatorias | Oportunidades |

`pip install -r requirements.txt` ya instala la librería (con PyTorch para CPU). El modelo
(~470 MB) se descarga solo la primera vez; para hacerlo de una vez y dejar calculados los vectores:

```bash
python -m scripts.indexar_embeddings
```

Los vectores se recalculan solos cuando cambia el texto de un proyecto, oportunidad o perfil.
Si el modelo no está disponible (sin internet la primera vez, o `EMBEDDINGS_ACTIVOS=false`), la
API usa similitud por palabras en común y la interfaz lo avisa. `GET /api/ia/estado` dice cuál se
está usando.

### Acceso, verificación de correo e ingreso con Google

Sin sesión solo se ve la página de bienvenida (`/bienvenida`) con cifras generales; proyectos,
personas, actores, oportunidades e IA exigen una cuenta con el correo confirmado.

- **Registro con correo y contraseña:** la API envía un enlace de confirmación (vence en 48 h). Sin
  `SMTP_HOST` en `backend/.env` no se envía nada y el enlace aparece en la consola de la API, lo
  que basta para desarrollar. Con Gmail: `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, el correo en
  `SMTP_USUARIO` y una [contraseña de aplicación](https://myaccount.google.com/apppasswords) en
  `SMTP_PASSWORD`.
- **Continuar con Google:** en [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
  crea un "ID de cliente de OAuth" de tipo *Aplicación web* con `http://localhost:5173` en
  "Orígenes de JavaScript autorizados" y copia el ID en `GOOGLE_CLIENT_ID`. La API valida la firma
  del token de Google y exige el dominio `@ufpso.edu.co`; esas cuentas quedan verificadas de una vez.
  Sin `GOOGLE_CLIENT_ID` el botón no aparece.
- Las cuentas que ya existían antes de la migración `0003` quedan verificadas.

### Perfil y alianzas

Cada usuario tiene **Mi perfil** (`/perfil`): sus datos, habilidades e intereses, los proyectos
que registró o donde colabora, sus alianzas y sugerencias personalizadas. Una alianza es una
solicitud para unirse a un proyecto (la responde quien lo registró) o una invitación (la responde
el invitado); al aceptarse, la persona queda como colaboradora del proyecto y el historial se
conserva con su estado.

### Correos verídicos

Antes de crear una cuenta, la API (`backend/app/core/validacion_correo.py`) revisa el formato,
corrige errores de tipeo frecuentes (`gmial.com` → «¿quisiste decir gmail.com?»), rechaza dominios
de correo temporal y consulta el DNS para confirmar que el dominio recibe correo (registros MX).
La interfaz repite las dos primeras revisiones al salir del campo. La prueba final es el enlace de
confirmación: una cuenta sin confirmar no aparta el correo, así que el dueño real siempre puede
registrarse.

### Colaboración con formato fijo y motivos

Pedir unirse a un proyecto o invitar a alguien usa siempre el mismo formulario: **rol o tipo de
aporte** (catálogo del admin), **qué aporta o qué se espera**, **habilidades**, **horas por semana**,
**motivación** y una nota opcional. El responsable (o el invitado) ve esa ficha en su perfil y en la
conversación de la solicitud, donde además hay **plantillas de mensaje** según quién escribe (lo que
va entre `[corchetes]` se selecciona para completarlo).

Aprobar o rechazar exige elegir un **motivo** del catálogo (unos para aprobar y otros para rechazar)
y admite un comentario, obligatorio si el motivo lo pide (p. ej. «Otro motivo»). Al aprobar, la
persona queda como miembro con el rol propuesto.

### Notificaciones (campana y correo)

Cada evento crea un aviso en la **campana** del encabezado (`/notificaciones` para verlos todos) y,
si corresponde, un **correo**:

- solicitud o invitación nueva → a quien debe responder, con la ficha completa;
- aprobada, rechazada o retirada → a la otra persona, con el motivo y el comentario;
- mensajes sin leer → un solo resumen por persona cuando llevan más de N minutos sin leerse
  (la API lo revisa cada `RESUMEN_INTERVALO_MINUTOS`; con `RESUMEN_AUTOMATICO=false` se puede lanzar
  con `python -m scripts.enviar_resumenes` o desde el panel de admin);
- cambios hechos por un admin (rol, cuenta desactivada o reactivada, proyecto retirado).

Cada persona elige en su perfil qué correos recibe (los de su cuenta llegan siempre). Sin SMTP, los
correos se imprimen en la consola de la API.

### Administración (`/admin`, solo rol admin)

- **Resumen:** usuarios, solicitudes por estado, tasa de aprobación, motivos y aportes más usados.
- **Usuarios:** buscar y filtrar, cambiar rol, activar o desactivar, marcar el correo como verificado,
  editar datos, enviar enlace para cambiar la contraseña y crear cuentas (les llega un correo para
  elegir contraseña). No se puede quitar el último administrador ni quitarse el rol a uno mismo.
- **Colaboración:** motivos de aprobación y rechazo, tipos de aporte y plantillas de mensaje
  (crear, editar, ordenar, activar o desactivar).
- **Áreas y ODS:** agregar, renombrar o eliminar áreas (no si están en uso) y renombrar los ODS.
- **Moderación:** retirar proyectos con un motivo que se le envía al responsable, y gestionar
  oportunidades y actores.
- **Ajustes:** dominios de correo permitidos para registrarse (reemplaza a `ALLOWED_EMAIL_DOMAINS`,
  que queda como valor inicial), interruptores de cada tipo de correo y minutos de espera del resumen.
- **Bitácora:** quién hizo qué y cuándo.

- **Roles y permisos** (solo el rol Administrador): matriz de permisos por acción para cada rol
  (registrar proyectos, pedir unirse, invitar, chats, ver actores/oportunidades/perfiles, IA,
  gestionar contenido y cada sección de este panel) y roles nuevos (p. ej. «Coordinador de
  semillero»), con opción de exigir correo institucional y de aparecer en el registro. El
  Administrador siempre tiene todo y «Roles y permisos» no se delega; quien gestiona usuarios no
  puede darse ni dar el rol de Administrador. La interfaz oculta lo que el rol no puede hacer y la
  API lo rechaza (403).
- **Insignias:** tres tipos visibles (Logro, Condecoración con aro dorado, Reconocimiento con aro
  punteado), 80 íconos con buscador y 13 colores. Pueden ser automáticas, con uno o varios
  requisitos combinados con «todos» o «al menos uno» (proyectos registrados, finalizados, en un
  área o con un ODS, colaboraciones, solicitudes aprobadas, personas sumadas, invitaciones
  aceptadas, horas comprometidas, mensajes, perfil completo, habilidades, antigüedad, rol, programa,
  otras insignias), o manuales: se otorgan a una persona, a varias o a todo el equipo de un proyecto,
  con motivo, fecha del evento y «en nombre de» (p. ej. una facultad). Pueden vencer en una fecha
  fija o a los N días. Se pueden retirar (una automática retirada no vuelve sola). La API revisa las
  automáticas cada `INSIGNIAS_INTERVALO_MINUTOS` (60) para requisitos que cambian solos. Cada persona las ve en «Mis logros» de su perfil, junto
  a su nombre en fichas y miembros, en su perfil público (`/personas/:id`) y en el ranking
  (`/logros`); al ganar una recibe aviso en la campana y por correo.

### Niveles y experiencia (XP)

- **Experiencia:** cada acción suma puntos según una tabla que el admin edita en «Niveles y XP»
  (puntos, tope por día y si está activa): entrar (una vez al día), completar el perfil, registrar,
  avanzar (cada 10 %) y finalizar proyectos, pedir unirse, invitar, ser aceptado, sumar personas,
  escribir en el chat (con tope), postular a convocatorias, quedar seleccionado, ganar insignias y
  evidencias aprobadas. Nada suma dos veces por lo mismo.
- **Niveles:** Novato, Curioso, Aprendiz, Colaborador, Descubridor, Conocedor, Experto, Genio y
  Leyenda, editables (nombre, ícono, color, XP mínima, cantidad de insignias y, si se quiere,
  insignias obligatorias). Se suben en orden; al subir llega aviso en la campana y por correo y se
  muestra una celebración. El nivel aparece junto al nombre, en «Mi nivel» del perfil (progreso,
  qué falta e historial) y en el ranking por XP de `/logros` (semana, mes o siempre).
- **Ajustes manuales:** el admin suma o resta XP con un motivo y ve el historial de cada persona.
- **Postulaciones:** el equipo de un proyecto lo postula a una oportunidad abierta explicando por
  qué encaja; quien gestiona oportunidades (Moderación) lo marca como seleccionado o no
  seleccionado (con comentario) y el equipo recibe aviso y XP.
- **Evidencias:** en el perfil y en cada proyecto se suben certificados, constancias, informes o
  fotos (PDF, PNG, JPG o WEBP hasta `ARCHIVO_MAX_MB`, 10 MB). El admin los revisa en «Evidencias»
  y decide cuánta XP dar o los rechaza con un motivo. Se guardan en `ARCHIVOS_DIR` (en producción,
  el volumen `archivos`; inclúyelo en las copias de seguridad).

El primer administrador se crea con `python -m scripts.create_admin correo@ufpso.edu.co "Nombre"`.

## Publicar en internet

Guía paso a paso en [`docs/despliegue-oracle.md`](docs/despliegue-oracle.md): una VM gratuita de
Oracle Cloud con `docker-compose.prod.yml` (PostgreSQL + pgvector, API, interfaz y HTTPS con Caddy).

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

- Editar proyectos y vincular actores desde la interfaz (la API ya lo permite).
- Perfiles con habilidades e intereses en la interfaz, para recomendar colaboradores.
- Búsqueda semántica y recomendación con embeddings (`pgvector`).
