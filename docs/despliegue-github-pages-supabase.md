# Despliegue: GitHub Pages + Render + Supabase

| Pieza | Dónde | Costo |
|---|---|---|
| Interfaz (React) | GitHub Pages — `https://<usuario>.github.io/<repositorio>/` | Gratis |
| API (FastAPI) | Render, plan gratuito (Docker, `render.yaml`) | Gratis, sin tarjeta |
| Base de datos (PostgreSQL + pgvector) | Supabase, plan gratuito | Gratis |

GitHub Pages solo publica archivos estáticos: no puede ejecutar la API de Python. Por eso la API
va en Render y la interfaz la consulta en la dirección guardada en la variable `VITE_API_URL`.
La interfaz nunca habla directo con Supabase; solo la API lo hace.

Ejemplo con este repositorio: interfaz en `https://josedgarciap.github.io/Proyecta/` y API en
`https://proyecta-api.onrender.com`. Cambia los nombres si los tuyos son distintos.

## 1. Supabase: copiar la cadena de conexión

1. En el proyecto de Supabase, botón **Connect** (arriba).
2. Pestaña **Connection string** → tipo **URI** → **Session pooler** (funciona con IPv4, que es lo
   que tiene Render; la conexión directa solo funciona con IPv6).
3. Copia la cadena. Se ve así:
   `postgresql://postgres.ginzvzfqupkqfybmaxsj:[YOUR-PASSWORD]@aws-0-<región>.pooler.supabase.com:5432/postgres`
4. Cambia `[YOUR-PASSWORD]` por la contraseña de la base (la puso quien creó el proyecto; si nadie
   la recuerda: **Project Settings → Database → Reset database password**). Si la contraseña tiene
   `@ : / ? # %`, escríbelos codificados (`@` → `%40`, `#` → `%23`, `%` → `%25`…).

No hace falta crear tablas a mano: la API aplica las migraciones (`alembic upgrade head`) cada vez
que arranca. La migración 0011 activa RLS y quita los permisos de los roles `anon` y `authenticated`,
así la API REST automática de Supabase no expone ninguna tabla.

## 2. Render: publicar la API

1. Entra a <https://render.com> con tu cuenta de GitHub.
2. **New → Blueprint** → elige el repositorio. Render lee `render.yaml` y pide los valores:
   - `DATABASE_URL`: la cadena del paso 1.
   - `FRONTEND_URL`: `https://josedgarciap.github.io/Proyecta` (sin barra al final).
   - `CORS_ORIGINS`: `https://josedgarciap.github.io` (solo el origen, sin `/Proyecta`).
   - `BREVO_API_KEY` y `SMTP_REMITENTE`: ver el paso 4 (se pueden dejar vacíos y llenarlos después).
   - `GOOGLE_CLIENT_ID`, `GROQ_API_KEY`: opcionales.
3. **Apply**. La primera construcción tarda unos minutos. Al terminar, abre
   `https://proyecta-api.onrender.com/api/salud`: debe responder `{"estado":"ok"}`.
4. En Supabase → **Table Editor** ya aparecen las tablas (`usuarios`, `proyectos`…).

## 3. GitHub Pages: publicar la interfaz

1. En GitHub, repositorio → **Settings → Pages** → **Source: GitHub Actions**.
2. **Settings → Secrets and variables → Actions → pestaña Variables → New repository variable**:
   - Nombre: `VITE_API_URL`
   - Valor: `https://proyecta-api.onrender.com` (sin barra al final)
3. Sube los cambios a `main` (o **Actions → Publicar en GitHub Pages → Run workflow**).
4. Cuando el flujo termine en verde, la página queda en `https://josedgarciap.github.io/Proyecta/`.

Si cambias `VITE_API_URL`, vuelve a ejecutar el flujo: la dirección se graba al compilar.

## 4. Correos (verificación de cuenta y avisos)

Render gratis bloquea los puertos SMTP, así que los correos salen por la API HTTPS de Brevo
(300 correos al día gratis):

1. Crea una cuenta en <https://www.brevo.com>.
2. **Senders, domains & dedicated IPs → Senders → Add a sender** con tu correo y confírmalo.
3. **SMTP & API → API Keys → Generate a new API key**.
4. En Render → servicio `proyecta-api` → **Environment**:
   - `BREVO_API_KEY` = la clave.
   - `SMTP_REMITENTE` = `Proyecta <el-correo-que-verificaste@gmail.com>`.

Sin esto, las cuentas creadas con correo y contraseña no reciben el enlace de verificación
(el ingreso con Google sí funciona, porque Google ya verifica el correo).

## 5. Primer administrador

Regístrate en la página y luego, en Supabase → **SQL Editor**:

```sql
UPDATE usuarios SET rol = 'admin', verificado = true WHERE email = 'tu-correo@ufpso.edu.co';
```

## 6. Ingreso con Google (opcional)

En Google Cloud Console → **Credentials** → el cliente OAuth → **Authorized JavaScript origins**:
agrega `https://josedgarciap.github.io`. Pon el mismo ID en `GOOGLE_CLIENT_ID` en Render.

## Límites del plan gratuito

- **Render** apaga la API tras 15 minutos sin visitas; la siguiente visita tarda ~1 minuto en
  despertarla. Los certificados y evidencias que se suben se guardan en el disco del servidor y
  **se pierden** cuando Render reinicia o vuelve a desplegar (para conservarlos habría que moverlos
  a Supabase Storage).
- **Supabase** pausa el proyecto tras 7 días sin actividad; se reactiva desde su panel.
- Sin el modelo de similitud semántica (no cabe en 512 MB): las sugerencias usan palabras en común.

Para un servidor que no se duerma y conserve los archivos, ver `docs/despliegue-oracle.md`
(también puede usar Supabase como base: basta con poner su cadena en `DATABASE_URL`).
