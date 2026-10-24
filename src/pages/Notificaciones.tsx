import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CheckCheck, Mail, Settings, Trash2 } from 'lucide-react'
import { eliminarAviso, listarAvisos, marcarAviso, marcarTodos } from '@/lib/notificaciones'
import { apiHabilitada } from '@/lib/http'
import type { Notificacion } from '@/lib/types'
import { EmptyState, Skeleton } from '@/components/ui'
import { hace, IconoAviso } from '@/components/IconoAviso'

const POR_PAGINA = 30

export function Notificaciones() {
  const [avisos, setAvisos] = useState<Notificacion[] | null>(null)
  const [soloNoLeidas, setSoloNoLeidas] = useState(false)
  const [hayMas, setHayMas] = useState(false)
  const [error, setError] = useState('')
  const navegar = useNavigate()

  const cargar = useCallback(() => {
    setAvisos(null)
    listarAvisos(soloNoLeidas, POR_PAGINA)
      .then((xs) => {
        setAvisos(xs)
        setHayMas(xs.length === POR_PAGINA)
      })
      .catch((e: Error) => setError(e.message))
  }, [soloNoLeidas])

  useEffect(() => {
    if (apiHabilitada) cargar()
  }, [cargar])

  if (!apiHabilitada) {
    return <EmptyState titulo="Las notificaciones necesitan la API" detalle="Conecta el backend (VITE_API_URL) e ingresa con tu cuenta." />
  }

  const masAntiguas = async () => {
    const xs = await listarAvisos(soloNoLeidas, POR_PAGINA, avisos?.length ?? 0)
    setAvisos((ys) => [...(ys ?? []), ...xs])
    setHayMas(xs.length === POR_PAGINA)
  }

  const abrir = (a: Notificacion) => {
    if (!a.leida) marcarAviso(a.id).catch(() => {})
    if (a.enlace) navegar(a.enlace)
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Notificaciones</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Solicitudes, respuestas, mensajes sin leer y avisos de tu cuenta.{' '}
            <Link to="/perfil#notificaciones" className="inline-flex items-center gap-1 text-brand-700 hover:underline dark:text-brand-300">
              <Settings size={13} aria-hidden /> Correos
            </Link>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="inline-flex rounded-md border border-slate-200 p-0.5 text-sm dark:border-slate-700" role="group" aria-label="Filtro">
            {[['Todas', false], ['Sin leer', true]].map(([etiqueta, valor]) => (
              <button key={String(valor)} onClick={() => setSoloNoLeidas(valor as boolean)} aria-pressed={soloNoLeidas === valor}
                className={`rounded px-3 py-1 ${soloNoLeidas === valor ? 'bg-brand-600 text-white dark:bg-brand-300 dark:text-brand-950' : 'text-slate-600 dark:text-slate-300'}`}>
                {etiqueta as string}
              </button>
            ))}
          </div>
          <button className="btn-ghost" onClick={() => marcarTodos().then(cargar)}>
            <CheckCheck size={15} aria-hidden /> Marcar todo como leído
          </button>
        </div>
      </header>

      {error && <p className="text-sm text-rose-600">{error}</p>}
      {avisos === null ? (
        <Skeleton className="h-64" />
      ) : avisos.length === 0 ? (
        <EmptyState titulo={soloNoLeidas ? 'Estás al día' : 'Sin notificaciones'} detalle="Aquí aparecerán las solicitudes, respuestas y avisos de la plataforma." />
      ) : (
        <ul className="card divide-y divide-slate-200 dark:divide-slate-800">
          {avisos.map((a) => (
            <li key={a.id} className={`group flex gap-3 px-5 py-4 ${a.leida ? '' : 'bg-brand-50/50 dark:bg-brand-500/5'}`}>
              <IconoAviso tipo={a.tipo} />
              <button className="min-w-0 flex-1 text-left" onClick={() => abrir(a)}>
                <span className={`block text-sm ${a.leida ? 'text-slate-700 dark:text-slate-300' : 'font-semibold text-slate-900 dark:text-white'}`}>{a.titulo}</span>
                {a.cuerpo && <span className="mt-0.5 block text-sm text-slate-600 dark:text-slate-400">{a.cuerpo}</span>}
                <span className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
                  {hace(a.creada_en)}
                  {a.correo_enviado && <><span aria-hidden>·</span><Mail size={12} aria-hidden /> enviado también por correo</>}
                </span>
              </button>
              <button className="self-start rounded p-1 text-slate-400 opacity-0 transition group-hover:opacity-100 hover:text-rose-600 focus:opacity-100"
                onClick={() => eliminarAviso(a.id).then(() => setAvisos((xs) => xs?.filter((x) => x.id !== a.id) ?? null))}
                aria-label="Eliminar notificación">
                <Trash2 size={15} aria-hidden />
              </button>
            </li>
          ))}
        </ul>
      )}
      {hayMas && <button className="btn-ghost mx-auto flex" onClick={masAntiguas}>Ver más antiguas</button>}
    </div>
  )
}
