import { useDatos } from '@/hooks/useDatos'
import { Badge, SectionTitle, Skeleton } from '@/components/ui'
import type { TipoActor } from '@/lib/types'

const TIPO_CLASS: Record<TipoActor, string> = {
  universidad: 'bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300',
  empresa: 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300',
  estado: 'bg-violet-100 text-violet-800 dark:bg-violet-500/15 dark:text-violet-300',
  comunidad: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  ong: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
}

export function Actores() {
  const { actores, cargando } = useDatos()

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Actores</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Aliados que acompañan, financian o ejecutan iniciativas registradas en la plataforma.
        </p>
      </header>

      <SectionTitle>{cargando ? 'Cargando…' : `${actores.length} actores registrados`}</SectionTitle>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {cargando
          ? Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-36" />)
          : actores.map((a) => (
              <article key={a.id} className="card p-5">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="font-semibold text-slate-900 dark:text-white">{a.nombre}</h2>
                  <Badge className={TIPO_CLASS[a.tipo]}>{a.tipo}</Badge>
                </div>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{a.sector}</p>
                <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">{a.contacto}</p>
                <p className="mt-3 text-xs text-slate-500 tabular-nums dark:text-slate-400">
                  {a.proyectos} proyecto(s) articulado(s)
                </p>
              </article>
            ))}
      </div>
    </div>
  )
}
