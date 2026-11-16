import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ExternalLink, Loader2, RotateCcw, Send, Sparkles, X } from 'lucide-react'
import { listarOportunidades } from '@/lib/api'
import { useAreas, useOds } from '@/lib/parametros'
import { buscarSemantico, obtenerPerfil } from '@/lib/colaboracion'
import { misPostulaciones } from '@/lib/experiencia'
import { usePuede } from '@/lib/permisos'
import { apiHabilitada } from '@/lib/http'
import { TIPOS_OPORTUNIDAD, TIPO_OPORTUNIDAD_LABEL, type Oportunidad, type Postulacion, type RespuestaSugerencias, type TipoOportunidad } from '@/lib/types'
import { EstadoPostulacionBadge, ListaPostulaciones, ModalPostular } from '@/components/Postulaciones'
import { NotaMetodo } from '@/components/Sugerencias'
import { Badge, EmptyState, Skeleton } from '@/components/ui'
import { diasRestantes, formatCompactCOP, formatDate } from '@/lib/format'

const TIPO_CLASS: Record<TipoOportunidad, string> = {
  convocatoria: 'bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300',
  financiacion: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  mentoria: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  infraestructura: 'bg-violet-100 text-violet-800 dark:bg-violet-500/15 dark:text-violet-300',
}

export function Oportunidades() {
  const areas = useAreas()
  const listaOds = useOds()
  // Filtros en la URL (se pueden compartir y sobreviven a recargar). Por defecto solo las vigentes.
  const [params, setParams] = useSearchParams()
  const tipo = (params.get('tipo') ?? '') as TipoOportunidad | ''
  const area = params.get('area') ?? ''
  const ods = Number(params.get('ods')) || 0
  const soloAbiertas = params.get('todas') !== '1'
  const hayFiltros = Boolean(tipo || area || ods || !soloAbiertas)

  const [oportunidades, setOportunidades] = useState<Oportunidad[]>([])
  const [cargando, setCargando] = useState(true)
  const [errorLista, setErrorLista] = useState('')
  const [consulta, setConsulta] = useState('')
  const [busqueda, setBusqueda] = useState<RespuestaSugerencias | null>(null)
  const [buscando, setBuscando] = useState(false)
  const [error, setError] = useState('')
  const puede = usePuede()
  const puedePostular = apiHabilitada && puede('oportunidades.postular')
  const [misProyectos, setMisProyectos] = useState<{ id: string; titulo: string }[] | null>(null)
  const [postulaciones, setPostulaciones] = useState<Postulacion[]>([])
  const [postulando, setPostulando] = useState<Oportunidad | null>(null)
  const [aviso, setAviso] = useState('')

  useEffect(() => {
    let vigente = true
    setCargando(true)
    setErrorLista('')
    listarOportunidades({ tipo: tipo || undefined, area: area || undefined, ods: ods || undefined, abiertas: soloAbiertas })
      .then((lista) => vigente && setOportunidades(lista))
      .catch((e) => vigente && setErrorLista((e as Error).message))
      .finally(() => vigente && setCargando(false))
    return () => { vigente = false }
  }, [tipo, area, ods, soloAbiertas])

  const actualizar = (clave: string, valor: string) => {
    const siguiente = new URLSearchParams(params)
    if (valor) siguiente.set(clave, valor)
    else siguiente.delete(clave)
    setParams(siguiente, { replace: true })
  }
  const restablecer = () => setParams(new URLSearchParams(), { replace: true })

  const cargarPostulaciones = useCallback(() => {
    misPostulaciones().then(setPostulaciones).catch(() => {})
  }, [])
  useEffect(() => {
    if (!puedePostular) return
    cargarPostulaciones()
    obtenerPerfil().then((p) => setMisProyectos(p.proyectos.map(({ proyecto }) => proyecto))).catch(() => setMisProyectos([]))
  }, [puedePostular, cargarPostulaciones])

  /** Postulaciones activas por oportunidad (las retiradas no cuentan). */
  const postuladosEn = (oid: string) => postulaciones.filter((p) => p.oportunidad_id === oid && p.estado !== 'retirada')

  const buscar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (consulta.trim().length < 3) return
    setBuscando(true)
    setError('')
    try {
      setBusqueda(await buscarSemantico(consulta.trim()))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBuscando(false)
    }
  }

  const relevancia = new Map(busqueda?.resultados.map((r) => [r.id, r.similitud]))
  const visibles = busqueda
    ? oportunidades.filter((o) => relevancia.has(o.id)).sort((a, b) => relevancia.get(b.id)! - relevancia.get(a.id)!)
    : oportunidades

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Oportunidades de apoyo</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Convocatorias, fondos, mentorías e infraestructura disponibles para las iniciativas registradas.
        </p>
      </header>

      {postulando && misProyectos && (
        <ModalPostular
          oportunidad={postulando}
          proyectos={misProyectos}
          yaPostulados={new Set(postuladosEn(postulando.id).map((p) => p.proyecto_id))}
          alCerrar={() => setPostulando(null)}
          alPostular={(p) => {
            setPostulando(null)
            setAviso(`«${p.proyecto_titulo}» quedó postulado a «${p.oportunidad_titulo}». Te avisaremos la respuesta.`)
            cargarPostulaciones()
          }}
        />
      )}
      {aviso && (
        <p role="status" className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-300">{aviso}</p>
      )}

      {puedePostular && postulaciones.length > 0 && (
        <section className="card p-5" id="mis-postulaciones">
          <h2 className="mb-1 flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
            <Send size={16} className="text-sky-600 dark:text-sky-400" aria-hidden /> Mis postulaciones
          </h2>
          <ListaPostulaciones postulaciones={postulaciones} mostrarProyecto puedeRetirar alCambiar={cargarPostulaciones} />
        </section>
      )}

      {apiHabilitada && (
        <form onSubmit={buscar} className="card p-4">
          <label htmlFor="busqueda-semantica" className="label flex items-center gap-1.5">
            <Sparkles size={13} aria-hidden /> Describe lo que buscas con tus palabras
          </label>
          <div className="flex gap-2">
            <input
              id="busqueda-semantica"
              className="input"
              placeholder="Ej.: dinero para un piloto de agua potable en zona rural"
              value={consulta}
              onChange={(e) => setConsulta(e.target.value)}
            />
            <button className="btn-primary shrink-0" disabled={buscando}>
              {buscando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Sparkles size={15} aria-hidden />}
              Buscar
            </button>
            {busqueda && (
              <button type="button" className="btn-ghost shrink-0" onClick={() => { setBusqueda(null); setConsulta('') }}>
                <X size={15} aria-hidden /> Ver todas
              </button>
            )}
          </div>
          {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
          {busqueda && (
            <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
              {busqueda.resultados.length} oportunidad(es) abiertas relacionadas, ordenadas por relevancia.
            </p>
          )}
          <NotaMetodo metodo={busqueda?.metodo} />
        </form>
      )}

      <div className="card flex flex-wrap items-end gap-3 p-4">
        <div className="w-48">
          <label className="label" htmlFor="f-tipo">Tipo</label>
          <select id="f-tipo" className="input" value={tipo} onChange={(e) => actualizar('tipo', e.target.value)}>
            <option value="">Todos</option>
            {TIPOS_OPORTUNIDAD.map((t) => <option key={t} value={t}>{TIPO_OPORTUNIDAD_LABEL[t]}</option>)}
          </select>
        </div>
        <div className="w-48">
          <label className="label" htmlFor="f-area">Área</label>
          <select id="f-area" className="input" value={area} onChange={(e) => actualizar('area', e.target.value)}>
            <option value="">Todas</option>
            {areas.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        <div className="min-w-56 flex-1">
          <label className="label" htmlFor="f-ods">ODS</label>
          <select id="f-ods" className="input" value={ods || ''} onChange={(e) => actualizar('ods', e.target.value)}>
            <option value="">Todos</option>
            {listaOds.map((o) => <option key={o.id} value={o.id}>{o.id}. {o.nombre}</option>)}
          </select>
        </div>
        <label className="flex h-10 cursor-pointer items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
          <input
            type="checkbox"
            className="h-4 w-4 accent-brand-600"
            checked={soloAbiertas}
            onChange={(e) => actualizar('todas', e.target.checked ? '' : '1')}
          />
          Solo abiertas
        </label>
        {hayFiltros && (
          <button type="button" className="btn-ghost h-10 text-sm" onClick={restablecer}>
            <RotateCcw size={14} aria-hidden /> Restablecer
          </button>
        )}
        <p className="basis-full text-xs text-slate-500 dark:text-slate-400" role="status">
          {cargando ? 'Cargando…' : `${visibles.length} ${visibles.length === 1 ? 'oportunidad' : 'oportunidades'}${soloAbiertas ? ' vigentes' : ''}`}
        </p>
      </div>

      {errorLista && <p className="text-sm text-rose-600">{errorLista}</p>}

      {!cargando && !errorLista && visibles.length === 0 && (
        hayFiltros || busqueda ? (
          <EmptyState
            titulo="Ninguna oportunidad coincide"
            detalle={soloAbiertas
              ? 'No hay convocatorias vigentes con esos filtros. Prueba con otros o incluye las que ya cerraron.'
              : 'Prueba con otro tipo, área u ODS.'}
            accion={<button className="btn-primary mt-2" onClick={() => { restablecer(); setBusqueda(null); setConsulta('') }}>Restablecer filtros</button>}
          />
        ) : (
          <EmptyState
            titulo="Aún no hay oportunidades abiertas"
            detalle="Cuando se publiquen convocatorias, fondos, mentorías o espacios de infraestructura, aparecerán aquí."
          />
        )
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {cargando
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-44" />)
          : visibles.map((o) => {
              const dias = diasRestantes(o.cierra_en)
              return (
                <article key={o.id} className="card flex flex-col gap-3 p-5">
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="font-semibold text-slate-900 dark:text-white">{o.titulo}</h2>
                    <div className="flex shrink-0 gap-1.5">
                      {relevancia.has(o.id) && (
                        <Badge className="bg-accent-100 text-accent-800 dark:bg-accent-500/15 dark:text-accent-300">
                          {Math.round(relevancia.get(o.id)! * 100)}% relevante
                        </Badge>
                      )}
                      <Badge className={TIPO_CLASS[o.tipo]}>{TIPO_OPORTUNIDAD_LABEL[o.tipo] ?? o.tipo}</Badge>
                    </div>
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
                        {formatDate(o.cierra_en)}{dias < 0 && ' · cerrada'}
                      </dd>
                    </div>
                  </dl>

                  {postuladosEn(o.id).length > 0 && (
                    <ul className="space-y-1 rounded-lg bg-slate-50 p-2 text-xs dark:bg-slate-900">
                      {postuladosEn(o.id).map((p) => (
                        <li key={p.id} className="flex items-center justify-between gap-2">
                          <span className="truncate text-slate-600 dark:text-slate-300">{p.proyecto_titulo}</span>
                          <EstadoPostulacionBadge p={p} />
                        </li>
                      ))}
                    </ul>
                  )}

                  <div className="flex flex-wrap items-center justify-between gap-2">
                    {o.url ? (
                      <a
                        href={o.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-700 hover:underline dark:text-brand-400"
                      >
                        Ver detalles <ExternalLink size={14} aria-hidden />
                      </a>
                    ) : <span />}
                    {puedePostular && dias >= 0 && (!misProyectos?.length || misProyectos.some((m) => !postuladosEn(o.id).some((p) => p.proyecto_id === m.id))) && (
                      <button className="btn-primary px-3 py-1.5 text-sm" disabled={!misProyectos} onClick={() => { setAviso(''); setPostulando(o) }}>
                        <Send size={14} aria-hidden /> Postular mi proyecto
                      </button>
                    )}
                  </div>
                </article>
              )
            })}
      </div>
    </div>
  )
}
