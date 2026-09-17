import { ExternalLink } from 'lucide-react'
import { useDatos } from '@/hooks/useDatos'
import { Badge, Skeleton } from '@/components/ui'
import { diasRestantes, formatCompactCOP, formatDate } from '@/lib/format'

const TIPO_CLASS: Record<string, string> = {
  convocatoria: 'bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300',
  financiacion: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  mentoria: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  infraestructura: 'bg-violet-100 text-violet-800 dark:bg-violet-500/15 dark:text-violet-300',
}

export function Oportunidades() {
  const { oportunidades, cargando } = useDatos()

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Oportunidades de apoyo</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Convocatorias, fondos, mentorías e infraestructura disponibles para las iniciativas registradas.
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {cargando
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-44" />)
          : oportunidades.map((o) => {
              const dias = diasRestantes(o.cierra_en)
              return (
                <article key={o.id} className="card flex flex-col gap-3 p-5">
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="font-semibold text-slate-900 dark:text-white">{o.titulo}</h2>
                    <Badge className={TIPO_CLASS[o.tipo]}>{o.tipo}</Badge>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{o.entidad}</p>

                  <div className="flex flex-wrap gap-1.5">
                    {o.areas.map((a) => (
                      <span key={a} className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-400">
                        {a}
                      </span>
                    ))}
                  </div>

                  <dl className="mt-auto grid grid-cols-2 gap-3 border-t border-slate-200 pt-3 text-sm dark:border-slate-800">
                    <div>
                      <dt className="label">Monto</dt>
                      <dd className="text-slate-700 tabular-nums dark:text-slate-300">
                        {o.monto ? formatCompactCOP(o.monto) : 'En especie'}
                      </dd>
                    </div>
                    <div>
                      <dt className="label">Cierre</dt>
                      <dd className={dias <= 30 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-700 dark:text-slate-300'}>
                        {formatDate(o.cierra_en)}
                      </dd>
                    </div>
                  </dl>

                  <a
                    href={o.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-700 hover:underline dark:text-brand-400"
                  >
                    Ver detalles <ExternalLink size={14} aria-hidden />
                  </a>
                </article>
              )
            })}
      </div>
    </div>
  )
}
