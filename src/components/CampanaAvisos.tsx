import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Bell, CheckCheck, Mail } from 'lucide-react'
import { listarAvisos, marcarAviso, marcarTodos } from '@/lib/notificaciones'
import type { Notificacion } from '@/lib/types'
import { hace, IconoAviso } from '@/components/IconoAviso'

/** Campana del header: avisos de solicitudes, respuestas, mensajes y cambios de cuenta. */
export function CampanaAvisos({ total }: { total: number }) {
  const [abierto, setAbierto] = useState(false)
  const [avisos, setAvisos] = useState<Notificacion[] | null>(null)
  const contenedor = useRef<HTMLDivElement>(null)
  const { pathname } = useLocation()
  const navegar = useNavigate()

  useEffect(() => setAbierto(false), [pathname])

  useEffect(() => {
    if (!abierto) return
    listarAvisos(false, 8).then(setAvisos).catch(() => setAvisos([]))
    const cerrar = (e: MouseEvent | KeyboardEvent) => {
      if (e instanceof KeyboardEvent ? e.key === 'Escape' : !contenedor.current?.contains(e.target as Node)) setAbierto(false)
    }
    document.addEventListener('mousedown', cerrar)
    document.addEventListener('keydown', cerrar)
    return () => {
      document.removeEventListener('mousedown', cerrar)
      document.removeEventListener('keydown', cerrar)
    }
  }, [abierto, total])

  const abrir = (a: Notificacion) => {
    if (!a.leida) marcarAviso(a.id).catch(() => {})
    setAbierto(false)
    navegar(a.enlace || '/notificaciones')
  }

  const leerTodo = async () => {
    await marcarTodos().catch(() => {})
    setAvisos((xs) => xs?.map((a) => ({ ...a, leida: true })) ?? null)
  }

  return (
    <div ref={contenedor} className="relative">
      <button
        onClick={() => setAbierto((x) => !x)}
        className={`btn-ghost relative px-2.5 ${total > 0 ? 'border-brand-300 text-brand-700 dark:border-brand-500/40 dark:text-brand-300' : ''}`}
        aria-label={total > 0 ? `${total} notificaciones sin leer` : 'Notificaciones'}
        aria-expanded={abierto}
        title="Notificaciones"
      >
        <Bell size={16} aria-hidden />
        {total > 0 && (
          <span className="absolute -top-1.5 -right-1.5 grid h-5 min-w-5 place-items-center rounded-full bg-rose-600 px-1 text-[11px] font-semibold text-white tabular-nums ring-2 ring-white dark:ring-slate-950">
            {total > 99 ? '99+' : total}
          </span>
        )}
      </button>

      {abierto && (
        <div className="card absolute right-0 z-30 mt-2 w-[min(22rem,calc(100vw-2rem))] overflow-hidden shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2.5 dark:border-slate-800">
            <p className="text-sm font-semibold text-slate-900 dark:text-white">Notificaciones</p>
            {total > 0 && (
              <button className="inline-flex items-center gap-1 text-xs text-brand-700 hover:underline dark:text-brand-300" onClick={leerTodo}>
                <CheckCheck size={13} aria-hidden /> Marcar todo como leído
              </button>
            )}
          </div>
          {avisos === null ? (
            <p className="px-4 py-6 text-center text-sm text-slate-500">Cargando…</p>
          ) : avisos.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-slate-500 dark:text-slate-400">No tienes notificaciones.</p>
          ) : (
            <ul className="max-h-96 divide-y divide-slate-200 overflow-y-auto dark:divide-slate-800">
              {avisos.map((a) => (
                <li key={a.id}>
                  <button onClick={() => abrir(a)} className={`flex w-full gap-3 px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-800/60 ${a.leida ? '' : 'bg-brand-50/60 dark:bg-brand-500/5'}`}>
                    <IconoAviso tipo={a.tipo} />
                    <span className="min-w-0 flex-1">
                      <span className={`block text-sm ${a.leida ? 'text-slate-700 dark:text-slate-300' : 'font-semibold text-slate-900 dark:text-white'}`}>{a.titulo}</span>
                      {a.cuerpo && <span className="line-clamp-2 text-xs text-slate-500 dark:text-slate-400">{a.cuerpo}</span>}
                      <span className="mt-0.5 flex items-center gap-1.5 text-[11px] text-slate-400">
                        {hace(a.creada_en)}
                        {a.correo_enviado && <><span aria-hidden>·</span><Mail size={11} aria-label="También se envió por correo" /></>}
                      </span>
                    </span>
                    {!a.leida && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-600 dark:bg-brand-300" aria-label="Sin leer" />}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <Link to="/notificaciones" className="block border-t border-slate-200 px-4 py-2.5 text-center text-sm text-brand-700 hover:bg-slate-50 dark:border-slate-800 dark:text-brand-300 dark:hover:bg-slate-800/60">
            Ver todas
          </Link>
        </div>
      )}
    </div>
  )
}
