import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Trophy } from 'lucide-react'
import { misLogros } from '@/lib/insignias'
import type { MisLogros as Datos } from '@/lib/types'
import { Skeleton } from '@/components/ui'
import { Medalla, TarjetaInsignia } from '@/components/Insignia'

/** «Mis logros» del perfil: insignias obtenidas, las automáticas en progreso y las que otorga la administración. */
export function MisLogros({ version }: { version?: unknown }) {
  const [datos, setDatos] = useState<Datos | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    misLogros().then(setDatos).catch((e: Error) => setError(e.message))
  }, [version])

  // Desde el aviso de una insignia nueva (/perfil#logros).
  useEffect(() => {
    if (datos && window.location.hash === '#logros') document.getElementById('logros')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [datos])

  return (
    <section id="logros" className="card scroll-mt-24 p-5">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <Trophy size={16} className="text-amber-600 dark:text-amber-400" aria-hidden /> Mis logros
          {datos && <span className="text-sm font-normal text-slate-500 tabular-nums">· {datos.obtenidas.length}</span>}
        </h2>
        <Link to="/logros" className="text-sm text-brand-700 hover:underline dark:text-brand-300">Ranking y todas las insignias</Link>
      </div>
      {error && <p className="text-sm text-rose-600">{error}</p>}
      {!datos && !error && <Skeleton className="h-32" />}
      {datos && (
        <div className="space-y-5">
          {datos.obtenidas.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">Aún no tienes insignias. Registra un proyecto, súmate a un equipo o completa tu perfil para ganar las primeras.</p>
          ) : (
            <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {datos.obtenidas.map((i) => <li key={i.id}><TarjetaInsignia i={i} /></li>)}
            </ul>
          )}
          {datos.en_progreso.length > 0 && (
            <div>
              <p className="label">En progreso</p>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {datos.en_progreso.map(({ insignia: i, modo, condiciones }) => (
                  <li key={i.id} className="flex min-w-0 items-start gap-3 rounded-lg border border-dashed border-slate-300 p-3 dark:border-slate-700">
                    <Medalla icono={i.icono} color={i.color} tipo={i.tipo} apagada />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{i.nombre}</p>
                      <p className="truncate text-xs text-slate-500 dark:text-slate-400">{i.descripcion}</p>
                      {condiciones.length > 1 && <p className="mt-1 text-[11px] text-slate-500">{modo === 'todas' ? 'Cumple todos:' : 'Cumple al menos uno:'}</p>}
                      <ul className="mt-1 space-y-1">
                        {condiciones.map((c) => (
                          <li key={c.texto}>
                            {condiciones.length > 1 && <p className="truncate text-[11px] text-slate-500" title={c.texto}>{c.texto}</p>}
                            <div className="flex items-center gap-2">
                              <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
                                <span className={`block h-full rounded-full ${c.actual >= c.umbral ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${(c.actual / c.umbral) * 100}%` }} />
                              </span>
                              <span className="text-[11px] text-slate-500 tabular-nums">{c.actual}/{c.umbral}</span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {datos.vencidas.length > 0 && (
            <div>
              <p className="label">Vencidas</p>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {datos.vencidas.map((i) => <li key={i.id}><TarjetaInsignia i={i} vencida /></li>)}
              </ul>
            </div>
          )}
          {datos.manuales_disponibles.length > 0 && (
            <div>
              <p className="label">Condecoraciones y reconocimientos que otorga la administración</p>
              <ul className="flex flex-wrap gap-2">
                {datos.manuales_disponibles.map((i) => (
                  <li key={i.id} className="flex items-center gap-2 rounded-full border border-slate-200 py-1 pr-3 pl-1 text-xs text-slate-600 dark:border-slate-800 dark:text-slate-300" title={i.descripcion}>
                    <Medalla icono={i.icono} color={i.color} tipo={i.tipo} tamano="sm" apagada /> {i.nombre}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </section>
  )
}
