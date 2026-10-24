import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'

/** Ventana modal con el estilo de la app. Escape o clic afuera la cierran. */
export function Modal({
  titulo, descripcion, children, alCerrar, ancho = 'max-w-lg',
}: { titulo: string; descripcion?: ReactNode; children: ReactNode; alCerrar: () => void; ancho?: string }) {
  const caja = useRef<HTMLDivElement>(null)
  const cerrar = useRef(alCerrar)
  cerrar.current = alCerrar

  // Solo al abrir: enfocar el primer campo, cerrar con Escape y bloquear el scroll de la página.
  useEffect(() => {
    const anterior = document.activeElement as HTMLElement | null
    caja.current?.querySelector<HTMLElement>('input, select, textarea, button:not([data-cerrar])')?.focus()
    const tecla = (e: KeyboardEvent) => e.key === 'Escape' && cerrar.current()
    document.addEventListener('keydown', tecla)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', tecla)
      document.body.style.overflow = overflow
      anterior?.focus?.()
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-slate-900/50 p-4 backdrop-blur-sm" onMouseDown={alCerrar}>
      <div
        ref={caja}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-titulo"
        className={`card my-8 w-full ${ancho} shadow-xl`}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div>
            <h2 id="modal-titulo" className="font-semibold text-slate-900 dark:text-white">{titulo}</h2>
            {descripcion && <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">{descripcion}</p>}
          </div>
          <button data-cerrar className="rounded p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" onClick={alCerrar} aria-label="Cerrar">
            <X size={18} aria-hidden />
          </button>
        </header>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  )
}
