import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Eye, FileBadge, Loader2, Paperclip, Trash2, Upload } from 'lucide-react'
import {
  ESTADO_EVIDENCIA, TIPO_EVIDENCIA, TIPOS_ARCHIVO, eliminarEvidencia, evidenciasDeProyecto, misEvidencias, subirEvidencia,
} from '@/lib/experiencia'
import { abrirArchivo } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import type { Evidencia, TipoEvidencia } from '@/lib/types'
import { Badge, Skeleton } from '@/components/ui'
import { useConfirmar } from '@/components/Confirmar'
import { formatDate } from '@/lib/format'

const MAX_MB = 10

export const tamano = (b: number) => (b >= 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`)

/** Botón que abre el archivo de una evidencia (lo descarga con la sesión). */
export function VerArchivo({ e, alError }: { e: Evidencia; alError?: (m: string) => void }) {
  const [abriendo, setAbriendo] = useState(false)
  return (
    <button className="btn-ghost px-2 py-1 text-xs" disabled={abriendo} title={e.archivo_nombre}
      onClick={() => {
        setAbriendo(true)
        abrirArchivo(`/evidencias/${e.id}/archivo`).catch((err: Error) => alError?.(err.message)).finally(() => setAbriendo(false))
      }}>
      {abriendo ? <Loader2 size={13} className="animate-spin" aria-hidden /> : <Eye size={13} aria-hidden />} Ver archivo
    </button>
  )
}

function Formulario({ proyectoId, proyectos, alSubir }: {
  proyectoId?: string; proyectos?: { id: string; titulo: string }[]; alSubir: () => void
}) {
  const [archivo, setArchivo] = useState<File | null>(null)
  const [titulo, setTitulo] = useState('')
  const [tipo, setTipo] = useState<TipoEvidencia>('certificado')
  const [descripcion, setDescripcion] = useState('')
  const [proyecto, setProyecto] = useState(proyectoId ?? '')
  const [estado, setEstado] = useState<'' | 'subiendo' | 'listo' | string>('')
  const entrada = useRef<HTMLInputElement>(null)

  const elegir = (f: File | null) => {
    setEstado('')
    if (f && f.size > MAX_MB * 1024 * 1024) {
      setEstado(`El archivo supera ${MAX_MB} MB`)
      return
    }
    setArchivo(f)
    if (f && !titulo) setTitulo(f.name.replace(/\.[^.]+$/, '').replace(/[_-]+/g, ' ').slice(0, 200))
  }

  const enviar = async (ev: React.FormEvent) => {
    ev.preventDefault()
    if (!archivo) return
    setEstado('subiendo')
    try {
      await subirEvidencia({ archivo, titulo: titulo.trim(), descripcion: descripcion.trim(), tipo, proyecto_id: proyecto || undefined })
      setArchivo(null)
      setTitulo('')
      setDescripcion('')
      if (entrada.current) entrada.current.value = ''
      setEstado('listo')
      alSubir()
    } catch (err) {
      setEstado((err as Error).message)
    }
  }

  return (
    <form onSubmit={enviar} className="space-y-3 rounded-lg border border-dashed border-slate-300 p-4 dark:border-slate-700">
      <label className="flex cursor-pointer items-center gap-3 rounded-lg bg-slate-50 p-3 text-sm hover:bg-slate-100 dark:bg-slate-900 dark:hover:bg-slate-800">
        <Paperclip size={16} className="text-slate-500" aria-hidden />
        <span className="min-w-0 flex-1 truncate">
          {archivo ? <><b>{archivo.name}</b> · {tamano(archivo.size)}</> : <span className="text-slate-500">Elegir archivo (PDF, PNG, JPG o WEBP, hasta {MAX_MB} MB)</span>}
        </span>
        <input ref={entrada} type="file" accept={TIPOS_ARCHIVO} className="sr-only" aria-label="Archivo"
          onChange={(e) => elegir(e.target.files?.[0] ?? null)} />
      </label>
      <div className="grid gap-3 sm:grid-cols-[1fr_10rem]">
        <label className="block">
          <span className="label">Título</span>
          <input className="input" required minLength={3} maxLength={200} value={titulo} onChange={(e) => setTitulo(e.target.value)}
            placeholder="Certificado de ponencia en el encuentro regional" />
        </label>
        <label className="block">
          <span className="label">Tipo</span>
          <select className="input" value={tipo} onChange={(e) => setTipo(e.target.value as TipoEvidencia)}>
            {Object.entries(TIPO_EVIDENCIA).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </label>
      </div>
      {!proyectoId && proyectos && proyectos.length > 0 && (
        <label className="block">
          <span className="label">Proyecto relacionado (opcional)</span>
          <select className="input" value={proyecto} onChange={(e) => setProyecto(e.target.value)}>
            <option value="">Ninguno</option>
            {proyectos.map((p) => <option key={p.id} value={p.id}>{p.titulo}</option>)}
          </select>
        </label>
      )}
      <label className="block">
        <span className="label">Descripción (opcional)</span>
        <textarea className="input min-h-16" maxLength={1000} value={descripcion} onChange={(e) => setDescripcion(e.target.value)}
          placeholder="Qué certifica, quién lo emitió y cuándo." />
      </label>
      <div className="flex flex-wrap items-center gap-3">
        <button className="btn-primary" disabled={!archivo || titulo.trim().length < 3 || estado === 'subiendo'}>
          {estado === 'subiendo' ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Upload size={15} aria-hidden />} Enviar a revisión
        </button>
        {estado === 'listo' && <span className="text-sm text-emerald-600">Enviada. La administración la revisará y decidirá la XP.</span>}
        {estado && !['subiendo', 'listo'].includes(estado) && <span className="text-sm text-rose-600">{estado}</span>}
      </div>
    </form>
  )
}

/**
 * Certificados y evidencias. Sin `proyectoId`: las mías (perfil). Con `proyectoId`: las del proyecto
 * (el equipo ve también las pendientes; los demás, solo las aprobadas).
 */
export function Evidencias({ proyectoId, puedeSubir, proyectos, titulo = 'Mis evidencias' }: {
  proyectoId?: string; puedeSubir: boolean; proyectos?: { id: string; titulo: string }[]; titulo?: string
}) {
  const { usuario } = useSesion()
  const [lista, setLista] = useState<Evidencia[] | null>(null)
  const [error, setError] = useState('')
  const [abierto, setAbierto] = useState(false)
  const { confirmar, ventana } = useConfirmar()

  const cargar = useCallback(() => {
    ;(proyectoId ? evidenciasDeProyecto(proyectoId) : misEvidencias()).then(setLista).catch((e: Error) => setError(e.message))
  }, [proyectoId])
  useEffect(cargar, [cargar])

  useEffect(() => {
    const id = proyectoId ? 'evidencias-proyecto' : 'evidencias'
    if (lista && window.location.hash === `#${id}`) document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [lista, proyectoId])

  const quitar = async (e: Evidencia) => {
    if (!(await confirmar({ titulo: '¿Eliminar esta evidencia?', detalle: `«${e.titulo}» y su archivo.`, aceptar: 'Eliminar', peligro: true }))) return
    try {
      await eliminarEvidencia(e.id)
      cargar()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const aprobadas = lista?.filter((e) => e.estado === 'aprobada') ?? []
  const xp = aprobadas.reduce((s, e) => s + e.xp_otorgada, 0)

  return (
    <section id={proyectoId ? 'evidencias-proyecto' : 'evidencias'} className="card scroll-mt-24 p-5">
      {ventana}
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-3">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <FileBadge size={16} className="text-brand-600 dark:text-brand-400" aria-hidden /> {titulo}
          {lista && lista.length > 0 && <span className="text-sm font-normal text-slate-500 tabular-nums">· {lista.length}</span>}
        </h2>
        {puedeSubir && (
          <button className="text-sm text-brand-700 hover:underline dark:text-brand-300" onClick={() => setAbierto((x) => !x)} aria-expanded={abierto}>
            {abierto ? 'Cancelar' : 'Adjuntar certificado'}
          </button>
        )}
      </div>
      <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
        {proyectoId
          ? 'Certificados, constancias, informes o fotos del proyecto. La administración los revisa y puede otorgar experiencia a quien los sube.'
          : 'Sube certificados, constancias o informes de lo que haces. La administración los revisa y decide cuánta experiencia otorgar.'}
        {!proyectoId && xp > 0 && <> Llevas <b>{xp.toLocaleString('es-CO')} XP</b> por evidencias.</>}
      </p>
      {abierto && puedeSubir && (
        <div className="mb-4">
          <Formulario proyectoId={proyectoId} proyectos={proyectos} alSubir={() => { setAbierto(false); cargar() }} />
        </div>
      )}
      {error && <p className="mb-2 text-sm text-rose-600">{error}</p>}
      {!lista && !error && <Skeleton className="h-20" />}
      {lista && lista.length === 0 && (
        <p className="text-sm text-slate-500 dark:text-slate-400">{proyectoId ? 'El proyecto aún no tiene evidencias.' : 'Aún no has subido evidencias.'}</p>
      )}
      {lista && lista.length > 0 && (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {lista.map((e) => {
            const [estadoTexto, estadoClase] = ESTADO_EVIDENCIA[e.estado]
            const mia = e.usuario_id === usuario?.id
            return (
              <li key={e.id} className="flex flex-wrap items-start gap-3 py-3">
                <div className="min-w-0 flex-1">
                  <p className="flex flex-wrap items-center gap-1.5 text-sm font-medium text-slate-900 dark:text-white">
                    {e.titulo}
                    <Badge className="bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{TIPO_EVIDENCIA[e.tipo]}</Badge>
                    <Badge className={estadoClase}>{estadoTexto}</Badge>
                    {e.estado === 'aprobada' && e.xp_otorgada > 0 && (
                      <Badge className="bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300">+{e.xp_otorgada} XP</Badge>
                    )}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {proyectoId ? `${e.usuario_nombre} · ` : ''}
                    {!proyectoId && e.proyecto_id && <><Link to={`/proyectos/${e.proyecto_id}`} className="hover:underline">{e.proyecto_titulo}</Link> · </>}
                    {formatDate(e.creado_en)} · {tamano(e.archivo_tamano)}
                  </p>
                  {e.descripcion && <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{e.descripcion}</p>}
                  {e.comentario && (
                    <p className={`mt-1 rounded-md px-2 py-1 text-xs ${e.estado === 'rechazada'
                      ? 'bg-rose-50 text-rose-800 dark:bg-rose-500/10 dark:text-rose-300' : 'bg-slate-50 text-slate-700 dark:bg-slate-900 dark:text-slate-300'}`}>
                      <b>{e.revisada_por ?? 'Administración'}:</b> {e.comentario}
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 gap-1">
                  <VerArchivo e={e} alError={setError} />
                  {mia && e.estado !== 'aprobada' && (
                    <button className="btn-ghost px-2 py-1 text-xs text-rose-700 dark:text-rose-400" onClick={() => quitar(e)} aria-label={`Eliminar ${e.titulo}`}>
                      <Trash2 size={13} aria-hidden />
                    </button>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
