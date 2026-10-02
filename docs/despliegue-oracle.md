# Publicar Proyecta en internet (Oracle Cloud Always Free)

Proyecta queda en una sola máquina virtual gratuita que no se apaga: la base de datos, la API y la interfaz,
con HTTPS automático. Tiempo aproximado: 1 a 2 horas la primera vez.

```
Navegador ──HTTPS──► Caddy (interfaz + certificado)
                       └── /api ──► API FastAPI ──► PostgreSQL + pgvector
                                         ├── Groq (IA para "Analizar", gratis)
                                         └── Gmail SMTP (correos de confirmación)
```

**Por qué Oracle y no GitHub Pages, Render o Supabase:** GitHub Pages solo sirve archivos estáticos (la interfaz), no la API
ni la base. Render gratis apaga la API tras 15 minutos sin uso y no deja enviar correos por SMTP. Supabase gratis pausa
la base después de una semana sin uso. La VM de Oracle (2 núcleos ARM y 12 GB de RAM) no vence ni se duerme, y ahí cabe
también el modelo de similitud semántica.

> Oracle pide una tarjeta solo para verificar la identidad. No cobra mientras uses recursos marcados como
> *Always Free*: no cambies la forma de la VM a una que no tenga esa etiqueta.

---

## 1. Crear la cuenta y la máquina virtual

1. Regístrate en https://signup.cloud.oracle.com. Como *Home Region* elige una cercana con buena disponibilidad
   (por ejemplo **US East (Ashburn)** o **Brazil East (São Paulo)**). La región de origen no se puede cambiar después.
2. En el menú: **Compute → Instances → Create instance**.
   - **Name:** `proyecta`
   - **Image:** *Canonical Ubuntu 24.04* (la versión que diga *aarch64*).
   - **Shape:** *Change shape → Ampere → VM.Standard.A1.Flex*, con **2 OCPU y 12 GB** de memoria (debe decir *Always Free-eligible*).
   - **Networking:** deja que cree la VCN y marca **Assign a public IPv4 address**.
   - **SSH keys:** *Generate a key pair for me* → **Save private key** (guárdala, por ejemplo en `Documentos\proyecta.key`).
   - **Create**.
   - Si sale *Out of capacity*, intenta en otro *Availability domain* o vuelve a intentar más tarde.
3. Cuando esté en verde (*Running*), copia la **Public IP address**.

### Abrir los puertos 80 y 443

En la página de la instancia: **Subnet → Security List (Default) → Add Ingress Rules**. Agrega dos reglas:

| Source CIDR | IP Protocol | Destination Port |
|---|---|---|
| `0.0.0.0/0` | TCP | `80` |
| `0.0.0.0/0` | TCP | `443` |

## 2. Un nombre gratuito con DuckDNS

Google y los certificados HTTPS necesitan un nombre, no una IP.

1. Entra a https://www.duckdns.org con tu cuenta de Google.
2. Crea un subdominio, por ejemplo `proyecta-ufpso`. En **current ip** pega la IP pública de la VM y pulsa **update ip**.
3. Tu dirección será `proyecta-ufpso.duckdns.org`.

## 3. Entrar a la VM desde Windows

En PowerShell (cambia la ruta de la llave y la IP):

```powershell
icacls "$HOME\Documents\proyecta.key" /inheritance:r /grant:r "$($env:USERNAME):R"
ssh -i "$HOME\Documents\proyecta.key" ubuntu@TU_IP_PUBLICA
```

Escribe `yes` la primera vez. Todo lo que sigue se ejecuta **dentro de la VM**.

## 4. Preparar la VM (una sola vez)

```bash
# Actualizar e instalar Docker
sudo apt update && sudo apt -y upgrade
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu

# Las imágenes Ubuntu de Oracle traen un firewall interno que bloquea 80/443: abrirlos
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save

# 4 GB de memoria de intercambio, por si acaso
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

exit
```

Vuelve a entrar con el mismo comando `ssh` (para que tome el grupo `docker`).

## 5. Descargar Proyecta y configurarlo

```bash
git clone https://github.com/mmi-cmd/Proyecta
cd Proyecta
cp deploy/produccion.env.example deploy/.env.produccion
openssl rand -hex 32   # copia el resultado para POSTGRES_PASSWORD
openssl rand -hex 32   # y este para SECRET_KEY
nano deploy/.env.produccion
```

Llena como mínimo `DOMINIO`, `POSTGRES_PASSWORD` y `SECRET_KEY`. Guarda con `Ctrl+O`, `Enter` y sal con `Ctrl+X`.

| Variable | De dónde sale |
|---|---|
| `DOMINIO` | `proyecta-ufpso.duckdns.org` (sin `https://`) |
| `SMTP_USUARIO` / `SMTP_PASSWORD` | Gmail del equipo + contraseña de aplicación (https://myaccount.google.com/apppasswords) |
| `GROQ_API_KEY` | https://console.groq.com/keys → *Create API Key* (gratis) |
| `GOOGLE_CLIENT_ID` | El mismo de la Parte 4d de la guía local (ver el paso 7) |

## 6. Encender

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion up -d --build
```

La primera vez tarda entre 10 y 15 minutos (descarga PyTorch y compila la interfaz). Revisa el estado con:

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion ps
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion logs -f api   # Ctrl+C para salir
```

Cuando `api` diga *healthy*, abre `https://proyecta-ufpso.duckdns.org`. Las migraciones se aplican solas al arrancar.

**Datos de ejemplo y administrador (opcional):**

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec api python -m scripts.seed_demo
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec api python -m scripts.create_admin tu.correo@ufpso.edu.co "Tu Nombre"
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec api python -m scripts.indexar_embeddings
```

## 7. Google: agregar la dirección pública

En https://console.cloud.google.com → **APIs y servicios → Credenciales →** tu ID de cliente OAuth:

- En *Orígenes de JavaScript autorizados* agrega `https://proyecta-ufpso.duckdns.org` (deja también `http://localhost:5173`).
- Mientras la app esté en modo *Prueba*, solo entran los correos que agregues en *Usuarios de prueba*. Para abrirla a todos,
  pulsa **Publicar aplicación** en la pantalla de consentimiento (como solo pide correo y nombre, no requiere revisión).

## 8. Mantenerlo

**Actualizar después de un merge a `main`:**

```bash
cd ~/Proyecta && sh deploy/actualizar.sh
```

**Copias de seguridad diarias** (guarda 14 días en `~/respaldos`):

```bash
mkdir -p ~/respaldos
(crontab -l 2>/dev/null; echo "30 3 * * * sh $HOME/Proyecta/deploy/respaldo.sh >> $HOME/respaldos/registro.log 2>&1") | crontab -
```

Restaurar una copia: `gunzip -c ~/respaldos/ARCHIVO.sql.gz | docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec -T db psql -U proyecta -d proyecta`

**Reinicios:** los contenedores tienen `restart: unless-stopped`, así que vuelven solos si la VM se reinicia.

## IA local en el servidor (opcional)

Si prefieres no depender de Groq: en `deploy/.env.produccion` pon `IA_PROVEEDOR=ollama` y luego:

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion --profile ollama up -d
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion exec ollama ollama pull llama3.2:3b
docker compose -f docker-compose.prod.yml --env-file deploy/.env.produccion up -d api
```

En 2 núcleos ARM cada análisis tarda entre 20 y 60 segundos. Groq responde en 1 o 2.

---

## Problemas comunes

| Síntoma | Solución |
|---|---|
| La página no carga (tiempo de espera agotado) | Revisa las reglas de la *Security List* (paso 1) y los `iptables` (paso 4). |
| Error de certificado o `ERR_SSL_PROTOCOL_ERROR` | DuckDNS no apunta a la IP correcta, o los puertos 80/443 están cerrados. Mira `docker compose ... logs web`. |
| `api` reinicia una y otra vez | `docker compose ... logs api`. Lo más común es un valor vacío o mal escrito en `deploy/.env.produccion`. |
| No llega el correo de confirmación | Revisa spam y `logs api`: si dice `No se pudo enviar`, revisa `SMTP_USUARIO` y la contraseña de aplicación. |
| "Analizar" dice "reglas locales" | Falta `GROQ_API_KEY` o se agotó el límite gratuito del día. |
| Google: `origin_mismatch` | Falta `https://TU_DOMINIO` en los orígenes autorizados (paso 7). |
| Oracle avisa que la instancia está inactiva | Oracle puede recuperar VMs gratuitas que pasan 7 días con CPU, red **y** memoria por debajo del 20 %. Con poco tráfico la memoria de la API (~1,5 GB) puede no alcanzar ese 20 % de 12 GB. Para evitarlo, activa el perfil de Ollama (sección anterior): mantiene ~3 GB en uso. |
