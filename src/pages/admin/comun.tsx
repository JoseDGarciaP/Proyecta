import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

/** Carga datos con estado de carga/error y una función para recargar. */
export function useCarga<T>(cargar: () => Promise<T>, deps: unknown[] = []) {
  const [datos, setDatos] = useState<T | null>(null)
  const [error, setError] = useState('')
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const recargar = useCallback(() => {
    setError('')
    return cargar().then(setDatos).catch((e: Error) => setError(e.message))
  }, deps)
  useEffect(() => {
    void recargar()
  }, [recargar])
  return { datos, error, recargar, setDatos }
}

export function Interruptor({ activo, alCambiar, etiqueta, disabled }: { activo: boolean; alCambiar: (v: boolean) => void; etiqueta: string; disabled?: boolean }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={activo}
      aria-label={etiqueta}
      disabled={disabled}
      onClick={() => alCambiar(!activo)}
      className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition disabled:opacity-50 ${activo ? 'bg-emerald-600' : 'bg-slate-300 dark:bg-slate-700'}`}
    >
      <span className={`inline-block h-4 w-4 rounded-full bg-white shadow transition ${activo ? 'translate-x-4.5' : 'translate-x-0.5'}`} />
    </button>
  )
}

export function Aviso({ tipo = 'error', children }: { tipo?: 'error' | 'ok'; children: ReactNode }) {
  if (!children) return null
  return (
    <p role={tipo === 'error' ? 'alert' : 'status'}
      className={`rounded-md px-3 py-2 text-sm ${tipo === 'error' ? 'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300' : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'}`}>
      {children}
    </p>
  )
}

export function BotonGuardar({ ocupado, children = 'Guardar' }: { ocupado: boolean; children?: ReactNode }) {
  return (
    <button className="btn-primary" disabled={ocupado}>
      {ocupado && <Loader2 size={15} className="animate-spin" aria-hidden />} {children}
    </button>
  )
}

export function Tarjeta({ titulo, descripcion, extra, children }: { titulo: string; descripcion?: ReactNode; extra?: ReactNode; children: ReactNode }) {
  return (
    <section className="card">
      <header className="flex items-start justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <div className="min-w-0 flex-1">
          <h2 className="font-semibold text-slate-900 dark:text-white">{titulo}</h2>
          {descripcion && <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{descripcion}</p>}
        </div>
        {extra && <div className="shrink-0">{extra}</div>}
      </header>
      <div className="p-5">{children}</div>
    </section>
  )
}

export const fechaHora = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
