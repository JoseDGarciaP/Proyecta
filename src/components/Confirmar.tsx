import { useEffect, useRef, useState, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Pregunta {
  titulo: string
  detalle?: string
  aceptar?: string
  peligro?: boolean
}

/**
 * Ventana de confirmación con el estilo de la app, en lugar del `confirm()` del navegador.
 * Uso: `const { confirmar, ventana } = useConfirmar()`, renderizar `ventana` y `if (await confirmar({...}))`.
 */
export function useConfirmar(): { confirmar: (p: Pregunta) => Promise<boolean>; ventana: ReactNode } {
  const [pregunta, setPregunta] = useState<(Pregunta & { responder: (si: boolean) => void }) | null>(null)

  const confirmar = (p: Pregunta) =>
    new Promise<boolean>((resolver) => setPregunta({ ...p, responder: resolver }))

  const cerrar = (si: boolean) => {
    pregunta?.responder(si)
    setPregunta(null)
  }

  return { confirmar, ventana: pregunta && <Ventana {...pregunta} cerrar={cerrar} /> }
}

function Ventana({ titulo, detalle, aceptar = 'Aceptar', peligro = false, cerrar }: Pregunta & { cerrar: (si: boolean) => void }) {
  const cancelar = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    cancelar.current?.focus()
    const tecla = (e: KeyboardEvent) => e.key === 'Escape' && cerrar(false)
    document.addEventListener('keydown', tecla)
    return () => document.removeEventListener('keydown', tecla)
  }, [cerrar])

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4 backdrop-blur-sm" onMouseDown={() => cerrar(false)}>
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirmar-titulo"
        className="card w-full max-w-sm p-6 shadow-xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex gap-3">
          {peligro && (
            <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-400">
              <AlertTriangle size={18} aria-hidden />
            </span>
          )}
          <div>
            <h2 id="confirmar-titulo" className="font-semibold text-slate-900 dark:text-white">{titulo}</h2>
            {detalle && <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{detalle}</p>}
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <button ref={cancelar} className="btn-ghost" onClick={() => cerrar(false)}>Cancelar</button>
          <button
            className={peligro ? 'btn bg-rose-600 text-white hover:bg-rose-700' : 'btn-primary'}
            onClick={() => cerrar(true)}
          >
            {aceptar}
          </button>
        </div>
      </div>
    </div>
  )
}
