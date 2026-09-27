/**
 * Cliente HTTP para la API de Proyecta (carpeta /backend).
 * Sin VITE_API_URL la app corre en modo demostración con datos locales.
 */
const base = import.meta.env.VITE_API_URL?.replace(/\/$/, '')

export const apiHabilitada = Boolean(base)

const CLAVE_TOKEN = 'proyecta_token'

export const token = {
  leer: () => localStorage.getItem(CLAVE_TOKEN),
  guardar: (t: string) => localStorage.setItem(CLAVE_TOKEN, t),
  borrar: () => localStorage.removeItem(CLAVE_TOKEN),
}

interface Opciones {
  method?: string
  json?: unknown
  form?: Record<string, string>
}

export async function pedir<T>(ruta: string, { method = 'GET', json, form }: Opciones = {}): Promise<T> {
  const headers: Record<string, string> = {}
  const t = token.leer()
  if (t) headers.Authorization = `Bearer ${t}`
  let body: BodyInit | undefined
  if (form) {
    body = new URLSearchParams(form)
  } else if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  }

  const res = await fetch(`${base}/api${ruta}`, { method, headers, body })
  if (res.status === 204) return undefined as T
  const datos = await res.json().catch(() => null)
  if (!res.ok) {
    const detalle = datos?.detail
    const mensaje = Array.isArray(detalle) ? detalle.map((d: { msg: string }) => d.msg).join(', ') : detalle
    throw new Error(mensaje || `Error ${res.status}`)
  }
  return datos as T
}
