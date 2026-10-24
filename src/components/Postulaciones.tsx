import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, Send } from 'lucide-react'
import { ESTADO_POSTULACION, postulacionesDeProyecto, postular, retirarPostulacion } from '@/lib/experiencia'
import type { Oportunidad, Postulacion } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { Badge, Skeleton } from '@/components/ui'
import { useConfirmar } from '@/components/Confirmar'
import { formatDate } from '@/lib/format'

/** Ventana para postular uno de mis proyectos a una oportunidad. */
export function ModalPostular({ oportunidad, proyectos, yaPostulados, alCerrar, alPostular }: {
  oportunidad: Pick<Oportunidad, 'id' | 'titulo' | 'entidad' | 'cierra_en'>
  proyectos: { id: string; titulo: string }[]
  yaPostulados: Set<string>
  alCerrar: () => void
  alPostular: (p: Postulacion) => void
}) {
  const disponibles = proyectos.filter((p) => !yaPostulados.has(p.id))
  const [proyecto, setProyecto] = useState(disponibles[0]?.id ?? '')
  const [nota, setNota] = useState('')
  const [estado, setEstado] = useState('')

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setEstado('enviando')
    try {
      alPostular(await postular(oportunidad.id, proyecto, nota.trim()))
    } catch (err) {
      setEstado((err as Error).message)
    }
  }

  return (
    <Modal titulo="Postular mi proyecto" descripcion={<>{oportunidad.titulo} · {oportunidad.entidad} · cierra el {formatDate(oportunidad.cierra_en)}</>} alCerrar={alCerrar}>
      {proyectos.length === 0 ? (
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Para postular necesitas ser parte del equipo de un proyecto. <Link to="/proyectos/nuevo" className="text-brand-700 underline dark:text-brand-300">Registra uno</Link> o súmate a un equipo.
        </p>
      ) : disponibles.length === 0 ? (
        <p className="text-sm text-slate-600 dark:text-slate-300">Todos tus proyectos ya están postulados a esta oportunidad.</p>
      ) : (
        <form onSubmit={enviar} className="space-y-4">
          <label className="block">
            <span className="label">Proyecto</span>
            <select className="input" value={proyecto} onChange={(e) => setProyecto(e.target.value)}>
              {disponibles.map((p) => <option key={p.id} value={p.id}>{p.titulo}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="label">¿Por qué encaja con esta oportunidad?</span>
            <textarea className="input min-h-28" required minLength={10} maxLength={1500} value={nota} onChange={(e) => setNota(e.target.value)}
              placeholder="Qué problema resuelve, en qué etapa está y cómo usaría el apoyo." />
            <span className="mt-1 block text-right text-[11px] text-slate-400 tabular-nums">{nota.length}/1500</span>
          </label>
          <p className="rounded-lg bg-brand-50 p-3 text-xs text-brand-800 dark:bg-brand-500/10 dark:text-brand-200">
            Quien gestiona la oportunidad revisará la postulación y el equipo recibirá la respuesta. Postular da experiencia y, si el proyecto queda seleccionado, todo el equipo gana más.
          </p>
          {estado && estado !== 'enviando' && <p className="text-sm text-rose-600">{estado}</p>}
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button>
            <button className="btn-primary" disabled={!proyecto || nota.trim().length < 10 || estado === 'enviando'}>
              {estado === 'enviando' ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Send size={15} aria-hidden />} Postular
            </button>
          </div>
        </form>
      )}
    </Modal>
  )
}

export function EstadoPostulacionBadge({ p }: { p: Postulacion }) {
  const [texto, clase] = ESTADO_POSTULACION[p.estado]
  return <Badge className={clase}>{texto}</Badge>
}

/** Lista de postulaciones (de una persona o de un proyecto). */
export function ListaPostulaciones({ postulaciones, mostrarProyecto, puedeRetirar, alCambiar }: {
  postulaciones: Postulacion[]; mostrarProyecto: boolean; puedeRetirar: boolean; alCambiar: () => void
}) {
  const { confirmar, ventana } = useConfirmar()
  const [error, setError] = useState('')

  const retirar = async (p: Postulacion) => {
    if (!(await confirmar({ titulo: '¿Retirar la postulación?', detalle: `«${p.proyecto_titulo}» en «${p.oportunidad_titulo}».`, aceptar: 'Retirar', peligro: true }))) return
    try {
      await retirarPostulacion(p.id)
      alCambiar()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <>
      {ventana}
      {error && <p className="mb-2 text-sm text-rose-600">{error}</p>}
      <ul className="divide-y divide-slate-100 dark:divide-slate-800">
        {postulaciones.map((p) => (
          <li key={p.id} className="flex flex-wrap items-start gap-3 py-3">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                {mostrarProyecto ? <><Link to={`/proyectos/${p.proyecto_id}`} className="hover:underline">{p.proyecto_titulo}</Link> → </> : ''}
                {p.oportunidad_titulo}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {p.oportunidad_entidad} · postulado el {formatDate(p.creado_en)}{p.usuario_nombre && ` por ${p.usuario_nombre}`}
              </p>
              {p.comentario && (
                <p className={`mt-1 rounded-md px-2 py-1 text-xs ${p.estado === 'no_seleccionada'
                  ? 'bg-rose-50 text-rose-800 dark:bg-rose-500/10 dark:text-rose-300' : 'bg-emerald-50 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-300'}`}>
                  {p.comentario}
                </p>
              )}
            </div>
            <EstadoPostulacionBadge p={p} />
            {puedeRetirar && p.estado === 'enviada' && (
              <button className="btn-ghost px-2 py-1 text-xs" onClick={() => retirar(p)}>Retirar</button>
            )}
          </li>
        ))}
      </ul>
    </>
  )
}

/** Postulaciones de un proyecto (el equipo ve todas; los demás, solo las seleccionadas). */
export function PostulacionesProyecto({ proyectoId, esEquipo }: { proyectoId: string; esEquipo: boolean }) {
  const [lista, setLista] = useState<Postulacion[] | null>(null)
  const cargar = useCallback(() => {
    postulacionesDeProyecto(proyectoId).then(setLista).catch(() => setLista([]))
  }, [proyectoId])
  useEffect(cargar, [cargar])

  if (lista && lista.length === 0 && !esEquipo) return null
  return (
    <section id="postulaciones" className="card scroll-mt-24 p-5">
      <div className="mb-2 flex items-baseline justify-between gap-3">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <Send size={16} className="text-sky-600 dark:text-sky-400" aria-hidden /> {esEquipo ? 'Postulaciones' : 'Seleccionado en'}
        </h2>
        {esEquipo && <Link to="/oportunidades" className="text-sm text-brand-700 hover:underline dark:text-brand-300">Buscar convocatorias</Link>}
      </div>
      {!lista ? <Skeleton className="h-16" /> : lista.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Aún no se ha postulado a ninguna oportunidad.</p>
      ) : (
        <ListaPostulaciones postulaciones={lista} mostrarProyecto={false} puedeRetirar={esEquipo} alCambiar={cargar} />
      )}
    </section>
  )
}
