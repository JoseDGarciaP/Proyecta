import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, CalendarDays, Users, Wallet } from 'lucide-react'
import { obtenerProyecto, listarActores, listarOportunidades } from '@/lib/api'
import { ODS, type Actor, type Oportunidad, type Proyecto } from '@/lib/types'
import { EstadoBadge, Progress, Skeleton, EmptyState } from '@/components/ui'
import { PanelIA } from '@/components/PanelIA'
import { formatCOP, formatDate } from '@/lib/format'

export function ProyectoDetalle() {
  const { id = '' } = useParams()
  const [proyecto, setProyecto] = useState<Proyecto | null>(null)
  const [actores, setActores] = useState<Actor[]>([])
  const [oportunidades, setOportunidades] = useState<Oportunidad[]>([])
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    let vigente = true
    setCargando(true)
    Promise.all([obtenerProyecto(id), listarActores(), listarOportunidades()])
      .then(([p, a, o]) => {
        if (!vigente) return
        setProyecto(p)
        setActores(a)
        setOportunidades(o)
      })
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [id])

  if (cargando) return <Skeleton className="h-96" />
  if (!proyecto) {
    return (
      <EmptyState
        titulo="Proyecto no encontrado"
        detalle="El registro solicitado no existe o fue eliminado."
        accion={<Link to="/proyectos" className="btn-primary mt-2">Volver al listado</Link>}
      />
    )
  }

  const vinculados = actores.filter((a) => proyecto.actores.includes(a.id))

  return (
    <div className="space-y-6">
      <Link to="/proyectos" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-brand-700 dark:text-slate-400 dark:hover:text-brand-400">
        <ArrowLeft size={15} aria-hidden /> Proyectos
      </Link>

      <header className="card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <EstadoBadge estado={proyecto.estado} />
              <span className="text-xs text-slate-500 dark:text-slate-400">{proyecto.area}</span>
            </div>
            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{proyecto.titulo}</h1>
            <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">{proyecto.resumen}</p>
          </div>
          <div className="w-full max-w-xs">
            <div className="mb-1 flex justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>Avance</span>
              <span className="tabular-nums">{proyecto.avance}%</span>
            </div>
            <Progress valor={proyecto.avance} />
          </div>
        </div>

        <dl className="mt-6 grid gap-4 border-t border-slate-200 pt-5 sm:grid-cols-3 dark:border-slate-800">
          <div>
            <dt className="label flex items-center gap-1.5"><Users size={13} aria-hidden /> Líder</dt>
            <dd className="text-sm text-slate-800 dark:text-slate-200">{proyecto.lider}</dd>
          </div>
          <div>
            <dt className="label flex items-center gap-1.5"><Wallet size={13} aria-hidden /> Presupuesto</dt>
            <dd className="text-sm text-slate-800 tabular-nums dark:text-slate-200">{formatCOP(proyecto.presupuesto)}</dd>
          </div>
          <div>
            <dt className="label flex items-center gap-1.5"><CalendarDays size={13} aria-hidden /> Periodo</dt>
            <dd className="text-sm text-slate-800 dark:text-slate-200">
              {formatDate(proyecto.fecha_inicio)} — {formatDate(proyecto.fecha_fin)}
            </dd>
          </div>
        </dl>
      </header>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="card p-6 lg:col-span-2">
          <h2 className="font-semibold text-slate-900 dark:text-white">Descripción</h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{proyecto.descripcion}</p>

          {proyecto.necesidades && (
            <>
              <h3 className="mt-6 label">Lo que necesita</h3>
              <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400">{proyecto.necesidades}</p>
            </>
          )}

          {proyecto.ods && proyecto.ods.length > 0 && (
            <>
              <h3 className="mt-6 label">ODS</h3>
              <ul className="flex flex-wrap gap-2">
                {proyecto.ods.map((n) => (
                  <li key={n} className="rounded-full bg-brand-50 px-3 py-1 text-xs text-brand-800 dark:bg-brand-500/12 dark:text-brand-200">
                    {n}. {ODS.find((o) => o.id === n)?.nombre}
                  </li>
                ))}
              </ul>
            </>
          )}

          <h3 className="mt-6 label">Equipo</h3>
          <ul className="flex flex-wrap gap-2">
            {proyecto.equipo.map((m) => (
              <li key={m} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                {m}
              </li>
            ))}
          </ul>

          <h3 className="mt-5 label">Etiquetas</h3>
          <ul className="flex flex-wrap gap-2">
            {proyecto.etiquetas.map((e) => (
              <li key={e} className="rounded-md border border-slate-200 px-2 py-0.5 text-xs text-slate-600 dark:border-slate-700 dark:text-slate-400">
                #{e}
              </li>
            ))}
          </ul>
        </section>

        <section className="card p-6">
          <h2 className="font-semibold text-slate-900 dark:text-white">Actores vinculados</h2>
          {vinculados.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Aún no hay actores articulados a este proyecto.</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {vinculados.map((a) => (
                <li key={a.id} className="text-sm">
                  <p className="font-medium text-slate-800 dark:text-slate-200">{a.nombre}</p>
                  <p className="text-xs text-slate-500 capitalize dark:text-slate-400">{a.tipo} · {a.sector}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <PanelIA proyecto={proyecto} oportunidades={oportunidades} />
    </div>
  )
}
