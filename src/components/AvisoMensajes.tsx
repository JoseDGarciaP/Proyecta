import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { MessageSquare } from 'lucide-react'
import type { NoLeidos } from '@/hooks/useNoLeidos'
import { enlaceDeChat } from '@/lib/chat'

const TITULO_BASE = document.title

/** Botón del header con los mensajes sin leer (equipos y solicitudes) y un menú para ir a cada chat. */
export function AvisoMensajes({ chats, total }: Pick<NoLeidos, 'chats' | 'total'>) {
  const [abierto, setAbierto] = useState(false)
  const contenedor = useRef<HTMLDivElement>(null)
  const { pathname } = useLocation()

  // El número también en la pestaña del navegador: «(3) Proyecta…».
  useEffect(() => {
    document.title = total > 0 ? `(${total}) ${TITULO_BASE}` : TITULO_BASE
    return () => {
      document.title = TITULO_BASE
    }
  }, [total])

  useEffect(() => setAbierto(false), [pathname])

  useEffect(() => {
    if (!abierto) return
    const cerrar = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !contenedor.current?.contains(e.target as Node)) {
        setAbierto(false)
      }
    }
    document.addEventListener('mousedown', cerrar)
    document.addEventListener('keydown', cerrar)
    return () => {
      document.removeEventListener('mousedown', cerrar)
      document.removeEventListener('keydown', cerrar)
    }
  }, [abierto])

  return (
    <div ref={contenedor} className="relative">
      <button
        onClick={() => setAbierto((x) => !x)}
        className={`btn-ghost relative px-2.5 ${total > 0 ? 'border-brand-300 text-brand-700 dark:border-brand-500/40 dark:text-brand-300' : ''}`}
        aria-label={total > 0 ? `${total} mensajes sin leer` : 'Mensajes'}
        aria-expanded={abierto}
        title="Mensajes de tus proyectos"
      >
        <MessageSquare size={16} aria-hidden />
        {total > 0 && (
          <span className="absolute -top-1.5 -right-1.5 grid h-5 min-w-5 place-items-center rounded-full bg-rose-600 px-1 text-[11px] font-semibold text-white tabular-nums ring-2 ring-white dark:ring-slate-950">
            <span className="absolute inset-0 animate-ping rounded-full bg-rose-500 opacity-40" aria-hidden />
            {total > 99 ? '99+' : total}
          </span>
        )}
      </button>

      {abierto && (
        <div className="card absolute right-0 z-30 mt-2 w-80 overflow-hidden">
          <p className="border-b border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-900 dark:border-slate-800 dark:text-white">
            Mensajes
          </p>
          {chats.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-slate-500 dark:text-slate-400">No tienes mensajes nuevos.</p>
          ) : (
            <ul className="max-h-96 divide-y divide-slate-200 overflow-y-auto dark:divide-slate-800">
              {chats.map((c) => (
                <li key={c.solicitud_id ?? c.proyecto_id}>
                  <Link to={enlaceDeChat(c)} className="block px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800/60">
                    <span className="flex items-center justify-between gap-2">
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium text-slate-900 dark:text-white">{c.titulo}</span>
                        {c.tipo === 'solicitud' && <span className="text-[11px] text-accent-700 dark:text-accent-300">Solicitud de colaboración</span>}
                      </span>
                      <span className="shrink-0 rounded-full bg-rose-600 px-1.5 text-xs font-semibold text-white tabular-nums">{c.no_leidos}</span>
                    </span>
                    {c.ultimo && (
                      <span className="mt-0.5 block truncate text-xs text-slate-500 dark:text-slate-400">
                        {c.ultimo.eliminado ? 'Mensaje eliminado' : `${c.ultimo.propio ? 'Tú' : c.ultimo.autor_nombre}: ${c.ultimo.texto}`}
                      </span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
