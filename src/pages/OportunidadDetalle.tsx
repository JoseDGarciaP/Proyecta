import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Building2, CalendarDays, ExternalLink, Send, Wallet } from 'lucide-react'
import { obtenerOportunidad } from '@/lib/api'
import { obtenerPerfil } from '@/lib/colaboracion'
import { misPostulaciones } from '@/lib/experiencia'
import { apiHabilitada } from '@/lib/http'
import { useOds } from '@/lib/parametros'
import { usePuede } from '@/lib/permisos'
import type { Oportunidad, Postulacion } from '@/lib/types'
import { DiasCierre, diasParaCierre } from '@/components/DiasCierre'
import { EstadoPostulacionBadge, ModalPostular } from '@/components/Postulaciones'
import { Badge, EmptyState, Skeleton } from '@/components/ui'
import { formatCOP, formatDate } from '@/lib/format'

const TIPO_LABEL: Record<Oportunidad['tipo'], string> = {
  convocatoria: 'Convocatoria',
  financiacion: 'Financiación',
  mentoria: 'Mentoría',
  infraestructura: 'Infraestructura',
}

/** Vista de detalle de una convocatoria u oportunidad dentro de la app (HU-04). */
export function OportunidadDetalle() {
  const { id = '' } = useParams()
  const [oportunidad, setOportunidad] = useState<Oportunidad | null>(null)
  const [cargando, setCargando] = useState(true)
  const catalogoOds = useOds()
  const puede = usePuede()
  const puedePostular = apiHabilitada && puede('oportunidades.postular')
  const [misProyectos, setMisProyectos] = useState<{ id: string; titulo: string }[] | null>(null)
  const [postulaciones, setPostulaciones] = useState<Postulacion[]>([])
  const [postulando, setPostulando] = useState(false)
  const [aviso, setAviso] = useState('')

  useEffect(() => {
    let vigente = true
    setCargando(true)
    obtenerOportunidad(id)
      .then((o) => vigente && setOportunidad(o))
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [id])

  const cargarPostulaciones = useCallback(() => {
    misPostulaciones().then(setPostulaciones).catch(() => {})
  }, [])
  useEffect(() => {
    if (!puedePostular) return
    cargarPostulaciones()
    obtenerPerfil().then((p) => setMisProyectos(p.proyectos.map(({ proyecto }) => proyecto))).catch(() => setMisProyectos([]))
  }, [puedePostular, cargarPostulaciones])

  if (cargando) return <Skeleton className="h-96" />
  if (!oportunidad) {
    return (
      <EmptyState
        titulo="Convocatoria no encontrada"
        detalle="Es posible que haya sido eliminada o que el enlace no sea correcto."
        accion={<Link to="/oportunidades" className="btn-primary mt-2">Volver a convocatorias</Link>}
      />
    )
  }

  const dias = diasParaCierre(oportunidad)
  const postulados = postulaciones.filter((p) => p.oportunidad_id === oportunidad.id && p.estado !== 'retirada')
  const quedanProyectos = !misProyectos?.length || misProyectos.some((m) => !postulados.some((p) => p.proyecto_id === m.id))
  const nombreOds = (n: number) => catalogoOds.find((o) => o.id === n)?.nombre ?? ''

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link to="/oportunidades" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-brand-700 dark:text-slate-400 dark:hover:text-brand-300">
        <ArrowLeft size={15} aria-hidden /> Convocatorias
      </Link>

      {postulando && misProyectos && (
        <ModalPostular
          oportunidad={oportunidad}
          proyectos={misProyectos}
          yaPostulados={new Set(postulados.map((p) => p.proyecto_id))}
          alCerrar={() => setPostulando(false)}
          alPostular={(p) => {
            setPostulando(false)
            setAviso(`«${p.proyecto_titulo}» quedó postulado a «${p.oportunidad_titulo}». Te avisaremos la respuesta.`)
            cargarPostulaciones()
          }}
        />
      )}
      {aviso && (
        <p role="status" className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-300">{aviso}</p>
      )}

      <header className="card space-y-4 p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{oportunidad.titulo}</h1>
            {oportunidad.entidad && (
              <p className="mt-1 inline-flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
                <Building2 size={14} aria-hidden /> {oportunidad.entidad}
              </p>
            )}
          </div>
          <div className="flex shrink-0 flex-wrap gap-1.5">
            <Badge className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">{TIPO_LABEL[oportunidad.tipo] ?? oportunidad.tipo}</Badge>
            <DiasCierre dias={dias} />
          </div>
        </div>

        <dl className="grid gap-4 border-t border-slate-200 pt-4 text-sm sm:grid-cols-3 dark:border-slate-800">
          <div>
            <dt className="label flex items-center gap-1.5"><CalendarDays size={13} aria-hidden /> Fecha de cierre</dt>
            <dd className="text-slate-700 dark:text-slate-300">{formatDate(oportunidad.cierra_en)}</dd>
          </div>
          <div>
            <dt className="label">Días para el cierre</dt>
            <dd className="text-slate-700 tabular-nums dark:text-slate-300">{dias < 0 ? 'Ya cerró' : dias}</dd>
          </div>
          <div>
            <dt className="label flex items-center gap-1.5"><Wallet size={13} aria-hidden /> Monto</dt>
            <dd className="text-slate-700 tabular-nums dark:text-slate-300">{oportunidad.monto ? formatCOP(oportunidad.monto) : 'En especie'}</dd>
          </div>
        </dl>

        <div className="flex flex-wrap gap-2 pt-1">
          {oportunidad.url && (
            <a href={oportunidad.url} target="_blank" rel="noreferrer" className="btn-ghost text-sm">
              <ExternalLink size={15} aria-hidden /> Abrir enlace oficial
            </a>
          )}
          {puedePostular && dias >= 0 && quedanProyectos && (
            <button className="btn-primary text-sm" disabled={!misProyectos} onClick={() => { setAviso(''); setPostulando(true) }}>
              <Send size={15} aria-hidden /> Postular mi proyecto
            </button>
          )}
        </div>
      </header>

      <section className="card space-y-3 p-6">
        <h2 className="font-semibold text-slate-900 dark:text-white">Descripción</h2>
        <p className="whitespace-pre-line text-sm text-slate-600 dark:text-slate-300">
          {oportunidad.descripcion?.trim() || 'Esta convocatoria no tiene descripción. Consulta el enlace oficial para conocer los términos.'}
        </p>
      </section>

      <section className="card grid gap-6 p-6 sm:grid-cols-2">
        <div>
          <h2 className="mb-2 font-semibold text-slate-900 dark:text-white">Áreas</h2>
          {oportunidad.areas.length ? (
            <div className="flex flex-wrap gap-1.5">
              {oportunidad.areas.map((a) => (
                <span key={a} className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-400">{a}</span>
              ))}
            </div>
          ) : <p className="text-sm text-slate-500">Abierta a todas las áreas.</p>}
        </div>
        <div>
          <h2 className="mb-2 font-semibold text-slate-900 dark:text-white">ODS</h2>
          {oportunidad.ods?.length ? (
            <ul className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
              {oportunidad.ods.map((n) => <li key={n}>ODS {n}{nombreOds(n) && ` · ${nombreOds(n)}`}</li>)}
            </ul>
          ) : <p className="text-sm text-slate-500">Sin ODS asociados.</p>}
        </div>
      </section>

      {postulados.length > 0 && (
        <section className="card p-6">
          <h2 className="mb-2 font-semibold text-slate-900 dark:text-white">Mis proyectos postulados</h2>
          <ul className="space-y-1 text-sm">
            {postulados.map((p) => (
              <li key={p.id} className="flex items-center justify-between gap-2">
                <span className="truncate text-slate-600 dark:text-slate-300">{p.proyecto_titulo}</span>
                <EstadoPostulacionBadge p={p} />
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
