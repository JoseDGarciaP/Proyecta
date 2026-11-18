import { Link } from 'react-router-dom'
import { Layers, Users } from 'lucide-react'
import type { Proyecto } from '@/lib/types'
import { useOds } from '@/lib/parametros'
import { EstadoBadge, Progress } from './ui'
import { formatCompactCOP } from '@/lib/format'

export function ProyectoCard({ proyecto }: { proyecto: Proyecto }) {
  const catalogoOds = useOds()
  const ods = proyecto.ods ?? []
  const nombreOds = (id: number) => catalogoOds.find((o) => o.id === id)?.nombre ?? `ODS ${id}`

  return (
    <Link
      to={`/proyectos/${proyecto.id}`}
      className="card group flex flex-col gap-3 p-5 transition hover:border-brand-600 dark:hover:border-brand-300"
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-semibold text-slate-900 group-hover:text-brand-700 dark:text-white dark:group-hover:text-brand-200">
          {proyecto.titulo}
        </h3>
        <EstadoBadge estado={proyecto.estado} />
      </div>

      <p className="line-clamp-2 text-sm text-slate-600 dark:text-slate-400">{proyecto.resumen}</p>

      <div className="flex flex-wrap items-center gap-1.5 text-xs">
        <span className="inline-flex items-center gap-1 rounded-md bg-brand-50 px-2 py-0.5 font-medium text-brand-800 dark:bg-brand-500/15 dark:text-brand-200">
          <Layers size={12} aria-hidden /> {proyecto.area}
        </span>
        {ods.slice(0, 4).map((id) => (
          <span
            key={id}
            title={nombreOds(id)}
            className="rounded-md bg-accent-50 px-2 py-0.5 font-medium text-accent-800 tabular-nums dark:bg-accent-500/15 dark:text-accent-200"
          >
            ODS {id}
          </span>
        ))}
        {ods.length > 4 && <span className="text-slate-500 dark:text-slate-400">+{ods.length - 4}</span>}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {proyecto.etiquetas.slice(0, 3).map((e) => (
          <span
            key={e}
            className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-400"
          >
            {e}
          </span>
        ))}
      </div>

      <div className="mt-auto space-y-2 pt-1">
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span className="inline-flex items-center gap-1.5" title="Responsable del proyecto">
            <Users size={13} aria-hidden /> {proyecto.lider}
            {proyecto.programa && <span className="text-slate-400">· {proyecto.programa}</span>}
          </span>
          <span className="tabular-nums">{formatCompactCOP(proyecto.presupuesto)}</span>
        </div>
        <Progress valor={proyecto.avance} />
        <p className="text-right text-xs text-slate-400 tabular-nums">{proyecto.avance}% de avance</p>
      </div>
    </Link>
  )
}
