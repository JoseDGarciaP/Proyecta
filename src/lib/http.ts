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
  /** Archivos y campos (multipart/form-data). */
  datos?: FormData
}

/** Error de la API con su código HTTP (p. ej. 403 = correo sin confirmar). */
export class ErrorApi extends Error {
  constructor(
    mensaje: string,
    readonly status: number,
  ) {
    super(mensaje)
  }
}

export async function pedir<T>(ruta: string, { method = 'GET', json, form, datos: multipart }: Opciones = {}): Promise<T> {
  const headers: Record<string, string> = {}
  const t = token.leer()
  if (t) headers.Authorization = `Bearer ${t}`
  let body: BodyInit | undefined
  if (multipart) {
    body = multipart  // el navegador pone el Content-Type con su «boundary»
  } else if (form) {
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
    throw new ErrorApi(mensaje || `Error ${res.status}`, res.status)
  }
  return datos as T
}

/** Descarga un archivo protegido (con el token) y lo abre en otra pestaña. */
export async function abrirArchivo(ruta: string): Promise<void> {
  const t = token.leer()
  const ventana = window.open('', '_blank')  // se abre ya para que el navegador no la bloquee
  const res = await fetch(`${base}/api${ruta}`, { headers: t ? { Authorization: `Bearer ${t}` } : {} })
  if (!res.ok) {
    ventana?.close()
    const datos = await res.json().catch(() => null)
    throw new ErrorApi(datos?.detail || `Error ${res.status}`, res.status)
  }
  const url = URL.createObjectURL(await res.blob())
  if (ventana) ventana.location.href = url
  else window.location.assign(url)
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
}
