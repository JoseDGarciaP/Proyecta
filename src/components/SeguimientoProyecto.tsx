import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { EyeOff, FileText, HandCoins, History, MessageSquareText, Paperclip, RotateCcw, Trash2, Upload } from 'lucide-react'
import {
  abrirAdjunto, borrarAdjunto, borrarAporte, listarAportes, registrarAporte, revisarAporte,
  type NuevoAporte, type ResumenAportes, borrarObservacion, crearObservacion, editarObservacion, eliminarProyecto, listarAdjuntos,
  listarCambios, listarObservaciones, ocultarObservacion, restaurarObservacion, subirAdjunto,
  type Adjunto, type CambioProyecto, type Observacion,
} from '@/lib/seguimiento'
import { useSesion } from '@/lib/sesion'
import { usePuede } from '@/lib/permisos'
import { formatCOP } from '@/lib/format'
import { useParametrosColaboracion } from '@/lib/parametros'

const fecha = (iso: string) => new Date(iso).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
const error = (e: unknown) => (e instanceof Error ? e.message : 'Algo falló')

/** Observaciones públicas sobre el proyecto, con edición propia y moderación (Ep4-Hu19, Ep4-Hu27). */
export function ObservacionesProyecto({ proyectoId }: { proyectoId: string }) {
  const { usuario } = useSesion()
  const puede = usePuede()
  const modera = puede('admin.moderacion')
  const [lista, setLista] = useState<Observacion[]>([])
  const [texto, setTexto] = useState('')
  const [editando, setEditando] = useState<{ id: string; texto: string } | null>(null)
  const [aviso, setAviso] = useState('')

  useEffect(() => {
    listarObservaciones(proyectoId).then(setLista).catch(() => setLista([]))
  }, [proyectoId])

  const reemplazar = (o: Observacion) => setLista((l) => l.map((x) => (x.id === o.id ? o : x)))

  async function enviar(e: React.FormEvent) {
    e.preventDefault()
    if (texto.trim().length < 2) return
    try {
      const o = await crearObservacion(proyectoId, texto.trim())
      setLista((l) => [...l, o])
      setTexto('')
      setAviso('')
    } catch (err) {
      setAviso(error(err))
    }
  }

  async function guardar() {
    if (!editando) return
    try {
      reemplazar(await editarObservacion(editando.id, editando.texto.trim()))
      setEditando(null)
    } catch (err) {
      setAviso(error(err))
    }
  }

  async function quitar(id: string) {
    if (!window.confirm('¿Borrar esta observación?')) return
    try {
      await borrarObservacion(id)
      setLista((l) => l.filter((x) => x.id !== id))
    } catch (err) {
      setAviso(error(err))
    }
  }

  async function ocultar(id: string) {
    const motivo = window.prompt('Motivo para ocultar la observación (se le avisa a quien la escribió):')
    if (!motivo || motivo.trim().length < 5) return
    try {
      reemplazar(await ocultarObservacion(id, motivo.trim()))
    } catch (err) {
      setAviso(error(err))
    }
  }

  return (
    <section className="card p-6">
      <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
        <MessageSquareText size={16} aria-hidden /> Observaciones
      </h2>
      {lista.length === 0 && <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Aún no hay observaciones.</p>}
      <ul className="mt-3 space-y-3">
        {lista.map((o) => (
          <li key={o.id} className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800">
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span><b className="text-slate-700 dark:text-slate-200">{o.autor}</b> · {fecha(o.creado_en)}{o.editado_en && ' · editada'}</span>
              <span className="flex gap-2">
                {usuario?.id === o.autor_id && !o.oculta && (
                  <button type="button" className="hover:text-brand-700" onClick={() => setEditando({ id: o.id, texto: o.texto })}>Editar</button>
                )}
                {(usuario?.id === o.autor_id || modera) && (
                  <button type="button" className="hover:text-red-600" onClick={() => quitar(o.id)}>Borrar</button>
                )}
                {modera && (o.oculta
                  ? <button type="button" className="inline-flex items-center gap-1 hover:text-brand-700" onClick={async () => reemplazar(await restaurarObservacion(o.id))}><RotateCcw size={12} aria-hidden /> Restaurar</button>
                  : <button type="button" className="inline-flex items-center gap-1 hover:text-amber-600" onClick={() => ocultar(o.id)}><EyeOff size={12} aria-hidden /> Ocultar</button>)}
              </span>
            </div>
            {editando?.id === o.id ? (
              <div className="mt-2 space-y-2">
                <textarea className="input" rows={3} value={editando.texto} onChange={(e) => setEditando({ id: o.id, texto: e.target.value })} />
                <div className="flex gap-2">
                  <button type="button" className="btn-primary text-xs" onClick={guardar}>Guardar</button>
                  <button type="button" className="btn-ghost text-xs" onClick={() => setEditando(null)}>Cancelar</button>
                </div>
              </div>
            ) : o.oculta ? (
              <p className="mt-1 italic text-slate-400">Observación oculta por moderación{o.motivo_oculta && `: ${o.motivo_oculta}`}{modera && ` — «${o.texto}»`}</p>
            ) : (
              <p className="mt-1 whitespace-pre-line text-slate-700 dark:text-slate-300">{o.texto}</p>
            )}
          </li>
        ))}
      </ul>
      {usuario && (
        <form onSubmit={enviar} className="mt-4 space-y-2">
          <label className="label" htmlFor="nueva-observacion">Deja una observación</label>
          <textarea id="nueva-observacion" className="input" rows={3} maxLength={3000} value={texto} onChange={(e) => setTexto(e.target.value)} />
          <button type="submit" className="btn-primary text-sm" disabled={texto.trim().length < 2}>Publicar</button>
        </form>
      )}
      {aviso && <p role="alert" className="mt-2 text-sm text-red-600">{aviso}</p>}
    </section>
  )
}

const kb = (n: number) => (n > 1_048_576 ? `${(n / 1_048_576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`)

/** Documentos e imágenes del proyecto: PDF, DOCX, PNG o JPG (Ep4-Hu21). */
export function AdjuntosProyecto({ proyectoId, puedeSubir }: { proyectoId: string; puedeSubir: boolean }) {
  const [lista, setLista] = useState<Adjunto[]>([])
  const [aviso, setAviso] = useState('')
  const [subiendo, setSubiendo] = useState(false)
  const entrada = useRef<HTMLInputElement>(null)

  useEffect(() => {
    listarAdjuntos(proyectoId).then(setLista).catch(() => setLista([]))
  }, [proyectoId])

  async function subir(archivo: File | undefined) {
    if (!archivo) return
    setSubiendo(true)
    setAviso('')
    try {
      const a = await subirAdjunto(proyectoId, archivo)
      setLista((l) => [a, ...l])
    } catch (err) {
      setAviso(error(err))
    } finally {
      setSubiendo(false)
      if (entrada.current) entrada.current.value = ''
    }
  }

  async function quitar(a: Adjunto) {
    if (!window.confirm(`¿Borrar «${a.nombre}»?`)) return
    try {
      await borrarAdjunto(a.id)
      setLista((l) => l.filter((x) => x.id !== a.id))
    } catch (err) {
      setAviso(error(err))
    }
  }

  return (
    <section className="card p-6">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white"><Paperclip size={16} aria-hidden /> Documentos adjuntos</h2>
        {puedeSubir && (
          <>
            <input ref={entrada} type="file" hidden accept=".pdf,.docx,.png,.jpg,.jpeg" onChange={(e) => subir(e.target.files?.[0])} />
            <button type="button" className="btn-ghost text-sm" disabled={subiendo} onClick={() => entrada.current?.click()}>
              <Upload size={14} aria-hidden /> {subiendo ? 'Subiendo…' : 'Subir'}
            </button>
          </>
        )}
      </div>
      {lista.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">No hay documentos. Se aceptan PDF, DOCX, PNG y JPG.</p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-200 text-sm dark:divide-slate-800">
          {lista.map((a) => (
            <li key={a.id} className="flex items-center justify-between gap-2 py-2">
              <button type="button" className="flex min-w-0 items-center gap-2 text-left hover:text-brand-700" onClick={() => abrirAdjunto(a).catch((e) => setAviso(error(e)))}>
                <FileText size={14} aria-hidden className="shrink-0" />
                <span className="truncate">{a.nombre}</span>
              </button>
              <span className="flex shrink-0 items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                {kb(a.tamano)} · {a.subido_por}
                {puedeSubir && (
                  <button type="button" aria-label={`Borrar ${a.nombre}`} className="hover:text-red-600" onClick={() => quitar(a)}><Trash2 size={13} aria-hidden /></button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}
      {aviso && <p role="alert" className="mt-2 text-sm text-red-600">{aviso}</p>}
    </section>
  )
}

/** Quién cambió qué y cuándo (Ep4-Hu18). */
export function HistorialProyecto({ proyectoId }: { proyectoId: string }) {
  const [lista, setLista] = useState<CambioProyecto[]>([])
  useEffect(() => {
    listarCambios(proyectoId).then(setLista).catch(() => setLista([]))
  }, [proyectoId])
  if (lista.length === 0) return null
  return (
    <section className="card p-6">
      <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white"><History size={16} aria-hidden /> Historial de cambios</h2>
      <ol className="mt-3 space-y-3 text-sm">
        {lista.map((c) => (
          <li key={c.id} className="border-l-2 border-brand-200 pl-3 dark:border-brand-500/40">
            <p className="text-xs text-slate-500 dark:text-slate-400"><b className="text-slate-700 dark:text-slate-200">{c.autor}</b> · {fecha(c.creado_en)}</p>
            <ul className="mt-1 space-y-0.5 text-slate-700 dark:text-slate-300">
              {c.cambios.map((x, i) => (
                <li key={i}><span className="font-medium">{x.campo}:</span> {x.antes ? <>{x.antes} → {x.despues}</> : x.despues}</li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </section>
  )
}

/** Botón para eliminar con motivo obligatorio; si hay colaboradores la API lo archiva (Ep4-Hu20). */
export function EliminarProyecto({ proyectoId, titulo }: { proyectoId: string; titulo: string }) {
  const navegar = useNavigate()
  const [abierto, setAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [aviso, setAviso] = useState('')

  async function confirmar() {
    try {
      await eliminarProyecto(proyectoId, motivo.trim())
      navegar('/proyectos')
    } catch (err) {
      setAviso(error(err))
    }
  }

  if (!abierto) {
    return (
      <button type="button" className="btn-ghost text-sm text-red-600" onClick={() => setAbierto(true)}>
        <Trash2 size={14} aria-hidden /> Eliminar
      </button>
    )
  }
  return (
    <div role="dialog" aria-modal="true" aria-labelledby="titulo-eliminar" className="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4">
      <div className="card w-full max-w-md space-y-3 p-6">
        <h2 id="titulo-eliminar" className="font-semibold text-slate-900 dark:text-white">Eliminar «{titulo}»</h2>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Si el proyecto tiene colaboradores, se archivará y se les avisará con el motivo. Si no, se borra definitivamente.
        </p>
        <label className="label" htmlFor="motivo-eliminar">Motivo</label>
        <textarea id="motivo-eliminar" className="input" rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
        {aviso && <p role="alert" className="text-sm text-red-600">{aviso}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost text-sm" onClick={() => setAbierto(false)}>Cancelar</button>
          <button type="button" className="btn-primary bg-red-600 text-sm hover:bg-red-700" disabled={motivo.trim().length < 5} onClick={confirmar}>
            Confirmar
          </button>
        </div>
      </div>
    </div>
  )
}

const hoy = () => new Date().toISOString().slice(0, 10)
const ESTADO_APORTE = {
  pendiente: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  validado: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  rechazado: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
}

/** Registro de aportes del equipo; el responsable los valida o rechaza (Ep6-Hu11). */
export function AportesProyecto({ proyectoId, esEquipo, esResponsable }: { proyectoId: string; esEquipo: boolean; esResponsable: boolean }) {
  const { usuario } = useSesion()
  const tipos = useParametrosColaboracion()?.tipos_aporte ?? []
  const [datos, setDatos] = useState<ResumenAportes | null>(null)
  const [abierto, setAbierto] = useState(false)
  const [form, setForm] = useState<NuevoAporte>({ tipo: '', descripcion: '', horas: null, valor: null, fecha: hoy() })
  const [aviso, setAviso] = useState('')

  const cargar = () => listarAportes(proyectoId).then(setDatos).catch(() => setDatos(null))
  useEffect(() => {
    listarAportes(proyectoId).then(setDatos).catch(() => setDatos(null))
  }, [proyectoId])

  async function enviar(e: React.FormEvent) {
    e.preventDefault()
    try {
      await registrarAporte(proyectoId, { ...form, tipo: form.tipo || tipos[0]?.nombre || 'Otro' })
      setForm({ tipo: '', descripcion: '', horas: null, valor: null, fecha: hoy() })
      setAbierto(false)
      setAviso('')
      cargar()
    } catch (err) {
      setAviso(error(err))
    }
  }

  async function revisar(id: string, accion: 'validar' | 'rechazar') {
    const comentario = accion === 'rechazar' ? window.prompt('¿Por qué no se valida este aporte?')?.trim() : ''
    if (accion === 'rechazar' && !comentario) return
    await revisarAporte(id, accion, comentario ?? '').then(cargar).catch((e) => setAviso(error(e)))
  }

  if (!datos) return null
  if (!esEquipo && datos.aportes.length === 0) return null
  return (
    <section className="card p-6">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white"><HandCoins size={16} aria-hidden /> Aportes del equipo</h2>
        {esEquipo && !abierto && <button type="button" className="btn-ghost text-sm" onClick={() => setAbierto(true)}>Registrar aporte</button>}
      </div>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        Validados: {datos.horas_validadas} h{datos.valor_validado > 0 && ` · ${formatCOP(datos.valor_validado)}`}
      </p>
      {abierto && (
        <form onSubmit={enviar} className="mt-3 grid gap-2 sm:grid-cols-2">
          <select className="input" aria-label="Tipo de aporte" value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
            {tipos.map((t) => <option key={t.id} value={t.nombre}>{t.nombre}</option>)}
            <option value="Otro">Otro</option>
          </select>
          <input type="date" className="input" aria-label="Fecha" max={hoy()} value={form.fecha} onChange={(e) => setForm({ ...form, fecha: e.target.value })} />
          <textarea className="input sm:col-span-2" rows={2} placeholder="¿Qué aportaste?" value={form.descripcion}
            onChange={(e) => setForm({ ...form, descripcion: e.target.value })} />
          <input type="number" min={0} className="input" placeholder="Horas" value={form.horas ?? ''}
            onChange={(e) => setForm({ ...form, horas: e.target.value ? Number(e.target.value) : null })} />
          <input type="number" min={0} className="input" placeholder="Valor en pesos (opcional)" value={form.valor ?? ''}
            onChange={(e) => setForm({ ...form, valor: e.target.value ? Number(e.target.value) : null })} />
          <div className="flex gap-2 sm:col-span-2">
            <button type="submit" className="btn-primary text-sm" disabled={form.descripcion.trim().length < 5}>Guardar</button>
            <button type="button" className="btn-ghost text-sm" onClick={() => setAbierto(false)}>Cancelar</button>
          </div>
        </form>
      )}
      <ul className="mt-3 divide-y divide-slate-200 text-sm dark:divide-slate-800">
        {datos.aportes.map((a) => (
          <li key={a.id} className="py-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span><b>{a.usuario}</b> · {a.tipo}{a.horas != null && ` · ${a.horas} h`}{a.valor != null && ` · ${formatCOP(a.valor)}`}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs ${ESTADO_APORTE[a.estado]}`}>{a.estado}</span>
            </div>
            <p className="text-slate-600 dark:text-slate-400">{a.descripcion}</p>
            {a.comentario && <p className="text-xs italic text-slate-500">«{a.comentario}»</p>}
            {a.estado === 'pendiente' && (
              <p className="mt-1 flex gap-3 text-xs">
                {esResponsable && (
                  <>
                    <button type="button" className="text-emerald-700 hover:underline" onClick={() => revisar(a.id, 'validar')}>Validar</button>
                    <button type="button" className="text-rose-700 hover:underline" onClick={() => revisar(a.id, 'rechazar')}>Rechazar</button>
                  </>
                )}
                {a.usuario_id === usuario?.id && (
                  <button type="button" className="text-slate-500 hover:underline" onClick={() => borrarAporte(a.id).then(cargar).catch((e) => setAviso(error(e)))}>Borrar</button>
                )}
              </p>
            )}
          </li>
        ))}
      </ul>
      {aviso && <p role="alert" className="mt-2 text-sm text-red-600">{aviso}</p>}
    </section>
  )
}
