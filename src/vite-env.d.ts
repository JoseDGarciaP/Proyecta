/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL del backend FastAPI, p. ej. http://localhost:8000. Vacío = modo demostración. */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
