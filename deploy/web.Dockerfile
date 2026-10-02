# Interfaz (React) compilada y servida por Caddy, que además pone HTTPS automático
# y reenvía /api a la API. Así todo queda en una sola dirección (sin problemas de CORS).
FROM node:22-alpine AS compilar
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=compilar /app/dist /srv
