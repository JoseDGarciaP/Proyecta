import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useDatos } from '@/hooks/useDatos'
import { apiHabilitada } from '@/lib/http'
import { listarAliados, type AliadoPublico } from '@/lib/aliados'
import { useAreas } from '@/lib/parametros'
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

      {apiHabilitada && <DirectorioAliados />}
    </div>
  )
}

/** Aliados externos verificados por un administrador, con filtro por sector y área (Ep4-Hu14). */
function DirectorioAliados() {
  const [sector, setSector] = useState('')
  const [interes, setInteres] = useState('')
  const [aliados, setAliados] = useState<AliadoPublico[] | null>(null)
  const areas = useAreas()
  useEffect(() => {
    const t = window.setTimeout(() => {
      listarAliados({ sector, interes }).then(setAliados).catch(() => setAliados([]))
    }, 250)
    return () => window.clearTimeout(t)
  }, [sector, interes])

  return (
    <section className="space-y-4">
      <SectionTitle>Aliados verificados</SectionTitle>
      <div className="flex flex-wrap gap-3">
        <input className="input w-56" placeholder="Filtrar por sector" value={sector} onChange={(e) => setSector(e.target.value)} aria-label="Sector" />
        <select className="input w-64" value={interes} onChange={(e) => setInteres(e.target.value)} aria-label="Área de interés">
          <option value="">Todas las áreas</option>
          {areas.map((a) => <option key={a}>{a}</option>)}
        </select>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {!aliados ? <Skeleton className="h-36" /> : aliados.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">No hay aliados verificados con esos filtros.</p>
        ) : aliados.map((a) => (
          <article key={a.usuario_id} className="card p-5">
            <div className="flex items-start justify-between gap-3">
              <h3 className="font-semibold text-slate-900 dark:text-white">
                <Link to={`/personas/${a.usuario_id}`} className="hover:underline">{a.razon_social || a.nombre}</Link>
              </h3>
              <Badge className="bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300">{a.tipo}</Badge>
            </div>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{a.sector}</p>
            {a.descripcion && <p className="mt-3 line-clamp-3 text-sm text-slate-600 dark:text-slate-400">{a.descripcion}</p>}
            {a.intereses.length > 0 && <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Interés: {a.intereses.join(', ')}</p>}
            {a.sitio_web && <a href={a.sitio_web} target="_blank" rel="noreferrer" className="mt-2 block text-xs text-brand-700 underline dark:text-brand-300">{a.sitio_web}</a>}
            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
              {a.proyectos.length ? `Apoya: ${a.proyectos.map((p) => p.titulo).join(', ')}` : 'Aún no apoya proyectos'}
            </p>
          </article>
        ))}
      </div>
    </section>
  )
}
