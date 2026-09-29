import { useEffect, useRef, useState } from 'react'
import { apiHabilitada, pedir } from '@/lib/http'
import { useTheme } from '@/hooks/useTheme'

interface ConfigAuth {
  google_client_id: string | null
  dominios: string[]
}

interface GoogleId {
  initialize: (opciones: Record<string, unknown>) => void
  renderButton: (elemento: HTMLElement, opciones: Record<string, unknown>) => void
}

declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } }
  }
}

let cargaScript: Promise<void> | null = null

function cargarGoogle(): Promise<void> {
  cargaScript ??= new Promise((resolver, rechazar) => {
    const script = document.createElement('script')
    script.src = 'https://accounts.google.com/gsi/client'
    script.async = true
    script.onload = () => resolver()
    script.onerror = () => rechazar(new Error('No se pudo cargar el ingreso con Google'))
    document.head.appendChild(script)
  })
  return cargaScript
}

/**
 * Botón oficial «Continuar con Google» (Google Identity Services). Entrega un ID token
 * que el backend verifica. No aparece si la API no tiene GOOGLE_CLIENT_ID configurado.
 */
export function BotonGoogle({ alIngresar }: { alIngresar: (credential: string) => void }) {
  const contenedor = useRef<HTMLDivElement>(null)
  const [config, setConfig] = useState<ConfigAuth | null>(null)
  const [error, setError] = useState('')
  const { tema } = useTheme()
  const callback = useRef(alIngresar)
  callback.current = alIngresar

  useEffect(() => {
    if (apiHabilitada) pedir<ConfigAuth>('/auth/config').then(setConfig).catch(() => setConfig(null))
  }, [])

  useEffect(() => {
    const clientId = config?.google_client_id
    if (!clientId || !contenedor.current) return
    cargarGoogle()
      .then(() => {
        const id = window.google!.accounts.id
        id.initialize({
          client_id: clientId,
          callback: ({ credential }: { credential: string }) => callback.current(credential),
          hd: config.dominios[0], // sugiere la cuenta institucional
          ux_mode: 'popup',
        })
        id.renderButton(contenedor.current!, {
          theme: tema === 'dark' ? 'filled_black' : 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'pill',
          locale: 'es',
          width: contenedor.current!.offsetWidth || 320,
        })
      })
      .catch((e: Error) => setError(e.message))
  }, [config, tema])

  if (!config?.google_client_id) return null
  return (
    <div className="space-y-3">
      <div ref={contenedor} className="flex min-h-11 justify-center" />
      {error && <p className="text-center text-xs text-rose-600">{error}</p>}
      <div className="flex items-center gap-3 text-xs text-slate-400">
        <span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" />o con tu correo y contraseña
        <span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" />
      </div>
    </div>
  )
}
