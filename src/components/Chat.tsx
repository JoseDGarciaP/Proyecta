import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Loader2, Lock, MessageSquare, Pencil, Send, Trash2 } from 'lucide-react'
import { INTERVALO_CHAT_MS, type ApiChat } from '@/lib/chat'
import { ErrorApi } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import type { Mensaje } from '@/lib/types'
import { useConfirmar } from '@/components/Confirmar'

const hora = new Intl.DateTimeFormat('es-CO', { dateStyle: 'short', timeStyle: 'short' })
const POR_PAGINA = 50

/** La modificación más reciente que se tiene (fechas ISO: se comparan como fechas, no como texto). */
function ultimaModificacion(mensajes: Mensaje[]): string | undefined {
  return mensajes.reduce<string | undefined>(
    (max, m) => (!max || Date.parse(m.modificado_en) > Date.parse(max) ? m.modificado_en : max),
    undefined,
  )
}

/** Une mensajes nuevos o actualizados con los que ya se muestran, por id y en orden. */
function unir(actuales: Mensaje[], nuevos: Mensaje[]): Mensaje[] {
  const cambia = nuevos.some((m) => {
    const actual = actuales.find((a) => a.id === m.id)
    return !actual || actual.modificado_en !== m.modificado_en
  })
  if (!cambia) return actuales // nada distinto: evita volver a dibujar cada 4 s
  const porId = new Map(actuales.map((m) => [m.id, m]))
  nuevos.forEach((m) => porId.set(m.id, m))
  return [...porId.values()].sort((a, b) => a.id - b.id)
}

interface Props {
  /** Identifica la conversación; al cambiar se vuelve a cargar. */
  clave: string
  crearApi: () => ApiChat
  titulo: string
  descripcion?: string
  /** Contenido extra bajo el título (p. ej. el perfil de la otra persona). */
  encabezado?: ReactNode
  /** Si viene, la conversación es de solo lectura y se muestra este aviso en lugar del campo de texto. */
  cerrada?: string
  vacio?: string
  id?: string
  alto?: string
}

/**
 * Conversación con consulta periódica: la usan el chat del equipo y el de cada solicitud.
 * Si la API responde 403 (no hace parte de la conversación) no se muestra nada.
 */
export function Chat({
  clave, crearApi, titulo, descripcion, encabezado, cerrada, id,
  vacio = 'Aún no hay mensajes. Escribe el primero.', alto = 'h-80',
}: Props) {
  const { usuario } = useSesion()
  const api = useMemo(crearApi, [clave]) // crearApi cambia en cada render; la conversación la define `clave`
  const { confirmar, ventana } = useConfirmar()
  const [mensajes, setMensajes] = useState<Mensaje[]>([])
  const [estado, setEstado] = useState<'cargando' | 'listo' | 'sin-acceso'>('cargando')
  const [hayAnteriores, setHayAnteriores] = useState(false)
  const [texto, setTexto] = useState('')
  const [editando, setEditando] = useState<Mensaje | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const lista = useRef<HTMLDivElement>(null)
  const alFinal = useRef(true)
  const ultimoId = mensajes.at(-1)?.id ?? 0
  const cambiosDesde = ultimaModificacion(mensajes)

  // Carga inicial: los últimos 50.
  useEffect(() => {
    if (!usuario) return
    let vigente = true
    setEstado('cargando')
    setMensajes([])
    api
      .listar()
      .then((ms) => {
        if (!vigente) return
        setMensajes(ms)
        setHayAnteriores(ms.length === POR_PAGINA)
        setEstado('listo')
      })
      .catch((e) => vigente && setEstado(e instanceof ErrorApi && e.status === 403 ? 'sin-acceso' : 'listo'))
    return () => {
      vigente = false
    }
  }, [api, usuario])

  // Consulta periódica de lo nuevo y de lo editado o eliminado; se pausa si la pestaña no está visible.
  const traerCambios = useCallback(
    () => api.listar({ despues_de: ultimoId, cambios_desde: cambiosDesde }).then((ms) => setMensajes((xs) => unir(xs, ms))),
    [api, ultimoId, cambiosDesde],
  )

  useEffect(() => {
    if (estado !== 'listo') return
    const consultar = () => document.visibilityState !== 'hidden' && traerCambios().catch(() => {})
    const intervalo = window.setInterval(consultar, INTERVALO_CHAT_MS)
    document.addEventListener('visibilitychange', consultar)
    return () => {
      window.clearInterval(intervalo)
      document.removeEventListener('visibilitychange', consultar)
    }
  }, [estado, traerCambios])

  // Al llegar mensajes: bajar si ya se estaba al final y marcarlos como leídos.
  useEffect(() => {
    if (!ultimoId) return
    const el = lista.current
    if (el && alFinal.current) el.scrollTop = el.scrollHeight
    api.marcarLeidos(ultimoId).catch(() => {})
  }, [api, ultimoId])

  // Desde un aviso de mensajes nuevos (enlace con #id), llevar la vista a la conversación ya cargada.
  useEffect(() => {
    if (id && estado === 'listo' && window.location.hash === `#${id}`) {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [id, estado])

  if (!usuario || estado === 'sin-acceso') return null

  const cargarAnteriores = async () => {
    const primero = mensajes[0]?.id
    if (!primero) return
    const el = lista.current
    const altoAntes = el?.scrollHeight ?? 0
    const anteriores = await api.listar({ antes_de: primero })
    setHayAnteriores(anteriores.length === POR_PAGINA)
    setMensajes((xs) => unir(xs, anteriores))
    // Mantener la vista donde estaba en lugar de saltar arriba.
    requestAnimationFrame(() => el && (el.scrollTop += el.scrollHeight - altoAntes))
  }

  const enviar = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!texto.trim() || enviando) return
    setEnviando(true)
    setError('')
    try {
      const m = editando ? await api.editar(editando.id, texto) : await api.enviar(texto)
      alFinal.current = true
      setMensajes((xs) => unir(xs, [m]))
      setTexto('')
      setEditando(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setEnviando(false)
    }
  }

  const eliminar = async (m: Mensaje) => {
    const si = await confirmar({
      titulo: '¿Eliminar este mensaje?',
      detalle: 'Se borrará para todas las personas de la conversación y en su lugar aparecerá «Mensaje eliminado».',
      aceptar: 'Eliminar',
      peligro: true,
    })
    if (!si) return
    try {
      await api.eliminar(m.id)
      // Se pide al servidor para quedarse con su fecha de modificación (la del navegador puede ir adelantada).
      await traerCambios()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const empezarEdicion = (m: Mensaje) => {
    setEditando(m)
    setTexto(m.texto)
  }

  return (
    <section id={id} className="card flex scroll-mt-24 flex-col">
      {ventana}
      <header className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <MessageSquare size={16} aria-hidden /> {titulo}
        </h2>
        {descripcion && <p className="text-xs text-slate-500 dark:text-slate-400">{descripcion}</p>}
        {encabezado}
      </header>

      <div
        ref={lista}
        onScroll={(e) => {
          const el = e.currentTarget
          alFinal.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40
        }}
        className={`${alto} space-y-3 overflow-y-auto px-5 py-4`}
        aria-live="polite"
      >
        {estado === 'cargando' ? (
          <p className="text-sm text-slate-500">Cargando…</p>
        ) : mensajes.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">{cerrada ? 'No hubo mensajes en esta conversación.' : vacio}</p>
        ) : (
          <>
            {hayAnteriores && (
              <button className="mx-auto block text-xs text-brand-700 hover:underline dark:text-brand-300" onClick={cargarAnteriores}>
                Ver mensajes anteriores
              </button>
            )}
            {mensajes.map((m) => (
              <article key={m.id} className={`group flex flex-col ${m.propio ? 'items-end' : 'items-start'}`}>
                <p className="mb-0.5 text-xs text-slate-500 dark:text-slate-400">
                  {m.propio ? 'Tú' : m.autor_nombre} · {hora.format(new Date(m.enviado_en))}
                  {m.editado_en && !m.eliminado && ' · editado'}
                </p>
                <div
                  className={`max-w-[80%] rounded-xl px-3 py-2 text-sm break-words whitespace-pre-wrap ${
                    m.eliminado
                      ? 'border border-dashed border-slate-300 text-slate-400 italic dark:border-slate-700'
                      : m.propio
                        ? 'bg-brand-600 text-white'
                        : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100'
                  }`}
                >
                  {m.eliminado ? 'Mensaje eliminado' : m.texto}
                </div>
                {!m.eliminado && (m.propio || usuario.rol === 'admin') && (
                  <div className="mt-1 flex gap-2 opacity-0 transition group-hover:opacity-100 focus-within:opacity-100">
                    {m.propio && !cerrada && (
                      <button className="text-xs text-slate-500 hover:text-brand-700" onClick={() => empezarEdicion(m)} aria-label="Editar mensaje">
                        <Pencil size={13} aria-hidden />
                      </button>
                    )}
                    <button className="text-xs text-slate-500 hover:text-rose-600" onClick={() => eliminar(m)} aria-label="Eliminar mensaje">
                      <Trash2 size={13} aria-hidden />
                    </button>
                  </div>
                )}
              </article>
            ))}
          </>
        )}
      </div>

      {cerrada ? (
        <p className="flex items-center gap-2 border-t border-slate-200 px-5 py-3 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
          <Lock size={13} aria-hidden /> {cerrada}
        </p>
      ) : (
        <form onSubmit={enviar} className="border-t border-slate-200 px-5 py-4 dark:border-slate-800">
          {editando && (
            <p className="mb-2 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
              Editando tu mensaje
              <button type="button" className="hover:underline" onClick={() => { setEditando(null); setTexto('') }}>
                Cancelar
              </button>
            </p>
          )}
          <div className="flex items-end gap-2">
            <textarea
              className="input max-h-40 min-h-10 resize-y"
              rows={1}
              maxLength={2000}
              placeholder="Escribe un mensaje (Enter envía, Shift+Enter cambia de línea)"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  enviar()
                }
              }}
              aria-label="Mensaje"
            />
            <button className="btn-primary" disabled={enviando || !texto.trim()} aria-label="Enviar">
              {enviando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Send size={15} aria-hidden />}
            </button>
          </div>
          {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
        </form>
      )}
    </section>
  )
}
