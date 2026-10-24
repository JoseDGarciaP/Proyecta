import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { perfilPublico } from '@/lib/insignias'
import { useSesion } from '@/lib/sesion'
import type { PerfilPublico } from '@/lib/types'
import { Badge, EmptyState, EstadoBadge, Skeleton } from '@/components/ui'
import { TarjetaInsignia } from '@/components/Insignia'
import { MedallaNivel } from '@/components/Nivel'

/** Perfil que ven las demás personas: datos, logros y proyectos donde participa. */
export function PerfilPersona() {
  const { id = '' } = useParams()
  const { usuario } = useSesion()
  const navegar = useNavigate()
  const [datos, setDatos] = useState<PerfilPublico | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setDatos(null)
    setError('')
    perfilPublico(id).then(setDatos).catch((e: Error) => setError(e.message))
  }, [id])

  if (error) return <EmptyState titulo="No se pudo abrir el perfil" detalle={error} />
  if (!datos) return <Skeleton className="h-96" />
  const { usuario: u, insignias, proyectos, nivel, xp } = datos
  const iniciales = u.nombre.split(' ').slice(0, 2).map((p) => p[0]).join('').toUpperCase()
  const etiquetas = [...u.habilidades.map((h) => ['h', h]), ...u.intereses.map((i) => ['i', i])]

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <button onClick={() => navegar(-1)} className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-brand-700 dark:text-slate-400">
        <ArrowLeft size={15} aria-hidden /> Volver
      </button>
      <header className="card flex flex-wrap items-center gap-5 p-6">
        <span className="grid h-16 w-16 place-items-center rounded-full bg-brand-600 text-xl font-semibold text-white dark:bg-brand-300 dark:text-brand-950">{iniciales}</span>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
            {u.nombre} {usuario?.id === u.id && <span className="text-sm font-normal text-slate-400">(tú)</span>}
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">{u.rol_nombre}{u.programa && ` · ${u.programa}`}</p>
          {u.bio && <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{u.bio}</p>}
          {etiquetas.length > 0 && (
            <ul className="mt-3 flex flex-wrap gap-1.5">
              {etiquetas.map(([t, e]) => (
                <li key={t + e}><Badge className={t === 'h' ? 'bg-brand-50 text-brand-800 dark:bg-brand-500/10 dark:text-brand-200' : 'bg-accent-50 text-accent-800 dark:bg-accent-500/10 dark:text-accent-200'}>{e}</Badge></li>
              ))}
            </ul>
          )}
        </div>
        <div className="flex items-center gap-6">
          {nivel && (
            <div className="flex items-center gap-3">
              <MedallaNivel nivel={nivel} />
              <div>
                <p className="text-xs text-slate-500">Nivel {nivel.posicion}</p>
                <p className="font-semibold text-slate-900 dark:text-white">{nivel.nombre}</p>
                <p className="text-xs text-slate-500 tabular-nums">{xp.toLocaleString('es-CO')} XP</p>
              </div>
            </div>
          )}
          <div className="text-center">
            <p className="text-3xl font-semibold text-slate-900 tabular-nums dark:text-white">{insignias.length}</p>
            <p className="text-xs text-slate-500">insignias</p>
          </div>
        </div>
      </header>

      <section className="card p-5">
        <h2 className="mb-3 font-semibold text-slate-900 dark:text-white">Logros</h2>
        {insignias.length === 0 ? <p className="text-sm text-slate-500">Todavía no tiene insignias.</p> : (
          <ul className="grid gap-2 sm:grid-cols-2">{insignias.map((i) => <li key={i.id}><TarjetaInsignia i={i} /></li>)}</ul>
        )}
      </section>

      <section className="card">
        <h2 className="border-b border-slate-200 px-5 py-4 font-semibold text-slate-900 dark:border-slate-800 dark:text-white">Proyectos</h2>
        {proyectos.length === 0 ? <p className="px-5 py-6 text-sm text-slate-500">No participa en proyectos todavía.</p> : (
          <ul className="divide-y divide-slate-200 dark:divide-slate-800">
            {proyectos.map(({ proyecto: p, rol }) => (
              <li key={p.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                <div className="min-w-0 flex-1">
                  <Link to={`/proyectos/${p.id}`} className="font-medium text-slate-900 hover:text-brand-700 dark:text-white dark:hover:text-brand-300">{p.titulo}</Link>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{p.area} · {rol}</p>
                </div>
                <EstadoBadge estado={p.estado} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
