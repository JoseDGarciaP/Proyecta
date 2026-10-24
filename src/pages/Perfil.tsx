import { useCallback, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Bell, Check, Handshake, Loader2, MessageCircle, MessageSquare, Send, Sparkles, UserRound, X } from 'lucide-react'
import {
  actualizarPerfil,
  listaATexto,
  obtenerPerfil,
  cancelarSolicitud,
  sugerenciasParaMi,
  textoALista,
} from '@/lib/colaboracion'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import type { Perfil as DatosPerfil, PreferenciasCorreo, Solicitud, SugerenciasParaMi } from '@/lib/types'
import { Badge, EmptyState, EstadoBadge, SectionTitle, Skeleton } from '@/components/ui'
import { ListaSugerencias, NotaMetodo } from '@/components/Sugerencias'
import { formatDate } from '@/lib/format'
import { useNoLeidos } from '@/hooks/useNoLeidos'
import { ChatSolicitud } from '@/components/ChatSolicitud'
import { DecidirSolicitud } from '@/components/DecidirSolicitud'
import { FichaRecomendacion } from '@/components/FichaRecomendacion'
import { useConfirmar } from '@/components/Confirmar'
import { guardarPreferencias, leerPreferencias } from '@/lib/notificaciones'
import { MisLogros } from '@/components/MisLogros'
import { InsigniasDe, NivelDe, NombrePersona } from '@/components/Insignia'
import { MiNivel } from '@/components/Nivel'
import { Evidencias } from '@/components/Evidencias'
import { usePuede } from '@/lib/permisos'

const ESTADO_SOLICITUD: Record<Solicitud['estado'], string> = {
  pendiente: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  aceptada: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  rechazada: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
  cancelada: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
}

export function Perfil() {
  const [perfil, setPerfil] = useState<DatosPerfil | null>(null)
  const [error, setError] = useState('')
  const { porProyecto: noLeidos, porSolicitud } = useNoLeidos()
  const puede = usePuede()

  const cargar = useCallback(() => {
    obtenerPerfil().then(setPerfil).catch((e: Error) => setError(e.message))
  }, [])

  useEffect(() => {
    if (apiHabilitada) cargar()
  }, [cargar])

  if (!apiHabilitada) {
    return (
      <EmptyState
        titulo="Tu perfil necesita la API"
        detalle="En modo demostración no hay cuentas. Conecta el backend (VITE_API_URL) e ingresa con tu correo para ver tus proyectos, alianzas y sugerencias."
      />
    )
  }
  if (error) return <EmptyState titulo="No se pudo cargar tu perfil" detalle={error} />
  if (!perfil) return <Skeleton className="h-96" />

  const { usuario, resumen } = perfil
  const iniciales = usuario.nombre.split(' ').slice(0, 2).map((p) => p[0]).join('').toUpperCase()

  return (
    <div className="space-y-6">
      <header className="card flex flex-wrap items-center gap-5 p-6">
        <span className="grid h-14 w-14 place-items-center rounded-full bg-brand-600 text-lg font-semibold text-white dark:bg-brand-300 dark:text-brand-950">
          {iniciales}
        </span>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{usuario.nombre}</h1>
          <p className="flex flex-wrap items-center gap-x-1 text-sm text-slate-500 dark:text-slate-400">
            {usuario.rol_nombre}
            {usuario.programa && ` · ${usuario.programa}`} · <span className="normal-case">{usuario.email}</span>
          </p>
          <p className="mt-1 flex flex-wrap items-center gap-2">
            <a href="#nivel" aria-label="Ver mi nivel"><NivelDe usuarioId={usuario.id} /></a>
            <a href="#logros"><InsigniasDe usuarioId={usuario.id} max={10} /></a>
          </p>
        </div>
        <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm sm:grid-cols-4">
          <Dato titulo="Proyectos" valor={resumen.proyectos} />
          <Dato titulo="Colaboraciones" valor={resumen.colaboraciones} />
          <Dato titulo="Alianzas activas" valor={resumen.alianzas_activas} />
          <Dato titulo="Por responder" valor={resumen.por_responder} resaltar={resumen.por_responder > 0} />
        </dl>
      </header>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          <section>
            <SectionTitle extra={<Link to="/proyectos/nuevo" className="text-sm text-brand-700 hover:underline dark:text-brand-300">Registrar otro</Link>}>
              Mis proyectos
            </SectionTitle>
            {perfil.proyectos.length === 0 ? (
              <EmptyState
                titulo="Aún no participas en proyectos"
                detalle="Registra uno o solicita unirte a un proyecto que te interese."
              />
            ) : (
              <ul className="card divide-y divide-slate-200 dark:divide-slate-800">
                {perfil.proyectos.map(({ proyecto, mi_rol }) => (
                  <li key={proyecto.id} className="flex flex-wrap items-center gap-3 px-5 py-4">
                    <div className="min-w-0 flex-1">
                      <Link to={`/proyectos/${proyecto.id}`} className="font-medium text-slate-900 hover:text-brand-700 dark:text-white dark:hover:text-brand-300">
                        {proyecto.titulo}
                      </Link>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{proyecto.area} · avance {proyecto.avance}%</p>
                    </div>
                    {noLeidos[proyecto.id] > 0 && (
                      <Link to={`/proyectos/${proyecto.id}#chat`} className="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline dark:text-brand-300">
                        <MessageSquare size={13} aria-hidden /> {noLeidos[proyecto.id]} {noLeidos[proyecto.id] === 1 ? 'mensaje nuevo' : 'mensajes nuevos'}
                      </Link>
                    )}
                    <EstadoBadge estado={proyecto.estado} />
                    <Badge className={mi_rol === 'responsable'
                      ? 'bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300'
                      : 'bg-accent-100 text-accent-800 dark:bg-accent-500/15 dark:text-accent-300'}>
                      {mi_rol === 'responsable' ? 'Responsable' : 'Colaborador'}
                    </Badge>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <MiNivel version={perfil} />
          <MisLogros version={perfil} />
          <Alianzas alianzas={perfil.alianzas} alCambiar={cargar} noLeidos={porSolicitud} />
          <Evidencias puedeSubir={puede('evidencias.subir')} proyectos={perfil.proyectos.map(({ proyecto }) => proyecto)} />
        </div>

        <div className="min-w-0 space-y-6">
          <EditarPerfil perfil={perfil} alGuardar={cargar} />
          <PreferenciasNotificaciones />
          {puede('ia.usar') && <ParaMi version={usuario} />}
        </div>
      </div>
    </div>
  )
}

function Dato({ titulo, valor, resaltar = false }: { titulo: string; valor: number; resaltar?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-slate-500 dark:text-slate-400">{titulo}</dt>
      <dd className={`text-xl font-semibold tabular-nums ${resaltar ? 'text-accent-600 dark:text-accent-400' : 'text-slate-900 dark:text-white'}`}>
        {valor}
      </dd>
    </div>
  )
}

function Alianzas({ alianzas, alCambiar, noLeidos }: { alianzas: Solicitud[]; alCambiar: () => void; noLeidos: Record<string, number> }) {
  const [ocupado, setOcupado] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [conversando, setConversando] = useState<Set<string>>(new Set())
  const [decidiendo, setDecidiendo] = useState<{ s: Solicitud; accion: 'aceptar' | 'rechazar' } | null>(null)
  const [detalle, setDetalle] = useState<Set<string>>(new Set())
  const { confirmar, ventana } = useConfirmar()
  const { hash } = useLocation()

  // Un aviso de mensajes lleva a /perfil#solicitud-<id>: abrir esa conversación.
  useEffect(() => {
    const id = hash.startsWith('#solicitud-') ? hash.slice('#solicitud-'.length) : ''
    if (!id) return
    setConversando((xs) => new Set(xs).add(id))
    // Desde un aviso de solicitud nueva: llevar la vista a esa tarjeta.
    requestAnimationFrame(() => document.getElementById(`alianza-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }))
  }, [hash])

  const alternarConversacion = (id: string) =>
    setConversando((xs) => {
      const nuevo = new Set(xs)
      if (!nuevo.delete(id)) nuevo.add(id)
      return nuevo
    })

  const botonConversar = (s: Solicitud) => (
    <button className="btn-ghost text-xs" onClick={() => alternarConversacion(s.id)} aria-expanded={conversando.has(s.id)}>
      <MessageCircle size={14} aria-hidden />
      {conversando.has(s.id) ? 'Ocultar conversación' : s.estado === 'pendiente' ? 'Conversar' : 'Ver conversación'}
      {noLeidos[s.id] > 0 && (
        <span className="rounded-full bg-rose-600 px-1.5 text-[11px] font-semibold text-white tabular-nums">{noLeidos[s.id]}</span>
      )}
    </button>
  )
  const porResponder = alianzas.filter((a) => a.por_responder)
  const resto = alianzas.filter((a) => !a.por_responder)

  const alternarDetalle = (id: string) =>
    setDetalle((xs) => {
      const nuevo = new Set(xs)
      if (!nuevo.delete(id)) nuevo.add(id)
      return nuevo
    })

  const cancelar = async (s: Solicitud) => {
    const si = await confirmar({
      titulo: `¿Retirar la ${s.tipo === 'solicitud' ? 'solicitud' : 'invitación'}?`,
      detalle: `«${s.proyecto_titulo}». Le avisaremos a la otra persona.`,
      aceptar: 'Retirar',
      peligro: true,
    })
    if (!si) return
    setOcupado(s.id)
    setError('')
    try {
      await cancelarSolicitud(s.id)
      alCambiar()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setOcupado(null)
    }
  }

  return (
    <section>
      {ventana}
      {decidiendo && (
        <DecidirSolicitud
          solicitud={decidiendo.s}
          accion={decidiendo.accion}
          alCerrar={() => setDecidiendo(null)}
          alDecidir={() => {
            setDecidiendo(null)
            alCambiar()
          }}
        />
      )}
      <SectionTitle>Alianzas</SectionTitle>
      {error && <p className="mb-2 text-sm text-rose-600">{error}</p>}
      {alianzas.length === 0 ? (
        <EmptyState
          titulo="Sin alianzas todavía"
          detalle="Cuando pidas unirte a un proyecto, invites a alguien o te inviten, aparecerá aquí con su estado."
        />
      ) : (
        <div className="space-y-4">
          {porResponder.length > 0 && (
            <ul className="space-y-2">
              {porResponder.map((s) => (
                <li key={s.id} id={`alianza-${s.id}`} className="card scroll-mt-24 border-accent-300 p-4 dark:border-accent-500/40">
                  <p className="text-sm text-slate-800 dark:text-slate-200">
                    <Handshake size={15} className="mr-1.5 inline text-accent-600" aria-hidden />
                    {s.tipo === 'solicitud' ? (
                      <><b><NombrePersona id={s.usuario_id} nombre={s.usuario_nombre} /></b> quiere unirse a <Link className="font-medium hover:underline" to={`/proyectos/${s.proyecto_id}`}>{s.proyecto_titulo}</Link></>
                    ) : (
                      <>Te invitaron a <Link className="font-medium hover:underline" to={`/proyectos/${s.proyecto_id}`}>{s.proyecto_titulo}</Link></>
                    )}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{formatDate(s.creado_en)}</p>
                  <div className="mt-3"><FichaRecomendacion solicitud={s} /></div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button className="btn bg-emerald-600 text-white hover:bg-emerald-700" disabled={ocupado === s.id} onClick={() => setDecidiendo({ s, accion: 'aceptar' })}>
                      <Check size={15} aria-hidden /> Aprobar
                    </button>
                    <button className="btn-ghost text-rose-700 dark:text-rose-400" disabled={ocupado === s.id} onClick={() => setDecidiendo({ s, accion: 'rechazar' })}>
                      <X size={15} aria-hidden /> Rechazar
                    </button>
                    {botonConversar(s)}
                  </div>
                  {conversando.has(s.id) && (
                    <div className="mt-3">
                      <ChatSolicitud solicitud={s} conFicha={false} />
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}

          {resto.length > 0 && (
            <ul className="card divide-y divide-slate-200 dark:divide-slate-800">
              {resto.map((s) => (
                <li key={s.id} id={`alianza-${s.id}`} className="flex scroll-mt-24 flex-wrap items-center gap-3 px-5 py-3 text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="text-slate-800 dark:text-slate-200">
                      {s.tipo === 'solicitud' ? `Solicitud de ${s.usuario_nombre}` : `Invitación a ${s.usuario_nombre}`} ·{' '}
                      <Link className="font-medium hover:underline" to={`/proyectos/${s.proyecto_id}`}>{s.proyecto_titulo}</Link>
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {formatDate(s.creado_en)}
                      {s.rol_propuesto && ` · ${s.rol_propuesto}`}
                      {s.motivo_nombre && <> · <span className="font-medium">Motivo:</span> {s.motivo_nombre}</>}
                      {s.respuesta && ` · «${s.respuesta}»`}
                    </p>
                  </div>
                  <Badge className={ESTADO_SOLICITUD[s.estado]}>{s.estado}</Badge>
                  <button className="btn-ghost text-xs" onClick={() => alternarDetalle(s.id)} aria-expanded={detalle.has(s.id)}>
                    {detalle.has(s.id) ? 'Ocultar detalle' : 'Detalle'}
                  </button>
                  {botonConversar(s)}
                  {s.estado === 'pendiente' && (
                    <button className="btn-ghost text-xs" disabled={ocupado === s.id} onClick={() => cancelar(s)}>
                      Retirar
                    </button>
                  )}
                  {detalle.has(s.id) && (
                    <div className="basis-full"><FichaRecomendacion solicitud={s} /></div>
                  )}
                  {conversando.has(s.id) && (
                    <div className="basis-full">
                      <ChatSolicitud solicitud={s} conFicha={!detalle.has(s.id)} />
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}

function EditarPerfil({ perfil, alGuardar }: { perfil: DatosPerfil; alGuardar: () => void }) {
  const { refrescar } = useSesion()
  const u = perfil.usuario
  const [programa, setPrograma] = useState(u.programa ?? '')
  const [bio, setBio] = useState(u.bio ?? '')
  const [habilidades, setHabilidades] = useState(listaATexto(u.habilidades))
  const [intereses, setIntereses] = useState(listaATexto(u.intereses))
  const [estado, setEstado] = useState<'' | 'guardando' | 'guardado' | string>('')

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault()
    setEstado('guardando')
    try {
      const nuevo = await actualizarPerfil({
        programa: programa.trim() || null,
        bio: bio.trim() || null,
        habilidades: textoALista(habilidades),
        intereses: textoALista(intereses),
      })
      refrescar(nuevo)
      alGuardar()
      setEstado('guardado')
    } catch (err) {
      setEstado((err as Error).message)
    }
  }

  return (
    <form onSubmit={guardar} className="card space-y-3 p-5">
      <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
        <UserRound size={16} aria-hidden /> Mi perfil
      </h2>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        La IA compara tus habilidades e intereses con lo que necesitan los proyectos.
      </p>
      <label className="block">
        <span className="label">Programa o dependencia</span>
        <input className="input" value={programa} onChange={(e) => setPrograma(e.target.value)} />
      </label>
      <label className="block">
        <span className="label">Habilidades (separadas por coma)</span>
        <input className="input" placeholder="Python, diseño de encuestas, SIG" value={habilidades} onChange={(e) => setHabilidades(e.target.value)} />
      </label>
      <label className="block">
        <span className="label">Intereses (separados por coma)</span>
        <input className="input" placeholder="agua potable, agroindustria" value={intereses} onChange={(e) => setIntereses(e.target.value)} />
      </label>
      <label className="block">
        <span className="label">Sobre mí</span>
        <textarea className="input min-h-20" value={bio} onChange={(e) => setBio(e.target.value)} />
      </label>
      <div className="flex items-center gap-3">
        <button className="btn-primary" disabled={estado === 'guardando'}>
          {estado === 'guardando' && <Loader2 size={15} className="animate-spin" aria-hidden />} Guardar
        </button>
        {estado === 'guardado' && <span className="text-sm text-emerald-600">Guardado</span>}
        {estado && !['guardando', 'guardado'].includes(estado) && <span className="text-sm text-rose-600">{estado}</span>}
      </div>
    </form>
  )
}

const PREFERENCIAS: { clave: keyof PreferenciasCorreo; titulo: string; detalle: string }[] = [
  { clave: 'solicitudes', titulo: 'Solicitudes e invitaciones nuevas', detalle: 'Cuando alguien pide unirse a tu proyecto, te invitan o (si revisas) llega algo por revisar.' },
  { clave: 'respuestas', titulo: 'Respuestas', detalle: 'Cuando responden una solicitud tuya, revisan tus evidencias o deciden una postulación.' },
  { clave: 'mensajes', titulo: 'Mensajes sin leer', detalle: 'Un resumen si te escribieron y no lo has leído en un rato.' },
  { clave: 'logros', titulo: 'Insignias y niveles', detalle: 'Cuando ganas una insignia, te otorgan un reconocimiento o subes de nivel.' },
]

/** Qué avisos llegan también al correo. Los de la campana llegan siempre. */
function PreferenciasNotificaciones() {
  const [prefs, setPrefs] = useState<PreferenciasCorreo | null>(null)
  const [estado, setEstado] = useState('')

  useEffect(() => {
    leerPreferencias().then(setPrefs).catch((e: Error) => setEstado(e.message))
  }, [])

  const cambiar = async (clave: keyof PreferenciasCorreo, valor: boolean) => {
    if (!prefs) return
    const anterior = prefs
    const nuevo = { ...prefs, [clave]: valor }
    setPrefs(nuevo)
    setEstado('')
    try {
      setPrefs(await guardarPreferencias(nuevo))
      setEstado('Guardado')
    } catch (e) {
      setPrefs(anterior)
      setEstado((e as Error).message)
    }
  }

  return (
    <section className="card space-y-3 p-5" id="notificaciones">
      <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
        <Bell size={16} aria-hidden /> Notificaciones por correo
      </h2>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Los avisos siempre aparecen en la campana. Elige cuáles quieres recibir también en tu correo.
      </p>
      {!prefs ? (
        <Skeleton className="h-24" />
      ) : (
        <ul className="space-y-2">
          {PREFERENCIAS.map((p) => (
            <li key={p.clave}>
              <label className="flex cursor-pointer items-start gap-3">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-brand-600" checked={prefs[p.clave]}
                  onChange={(e) => cambiar(p.clave, e.target.checked)} />
                <span className="text-sm">
                  <span className="font-medium text-slate-800 dark:text-slate-200">{p.titulo}</span>
                  <span className="block text-xs text-slate-500 dark:text-slate-400">{p.detalle}</span>
                </span>
              </label>
            </li>
          ))}
        </ul>
      )}
      {estado && <p className={`text-xs ${estado === 'Guardado' ? 'text-emerald-600' : 'text-rose-600'}`}>{estado}</p>}
    </section>
  )
}

/** `version` cambia al guardar el perfil, para volver a calcular las sugerencias. */
function ParaMi({ version }: { version: unknown }) {
  const [datos, setDatos] = useState<SugerenciasParaMi | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    setDatos(null)
    sugerenciasParaMi().then(setDatos).catch((e: Error) => setError(e.message))
  }, [version])

  return (
    <section className="card p-5">
      <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
        <Sparkles size={16} className="text-brand-600 dark:text-brand-400" aria-hidden /> Sugerencias para ti
      </h2>
      {error && <p className="mt-2 text-sm text-rose-600">{error}</p>}
      {!datos && !error && <Skeleton className="mt-3 h-32" />}
      {datos && (
        <div className="mt-3 space-y-4">
          {!datos.perfil_completo && (
            <p className="rounded-lg bg-brand-50 p-3 text-xs text-brand-800 dark:bg-brand-500/12 dark:text-brand-200">
              <Send size={12} className="mr-1 inline" aria-hidden />
              Completa tus habilidades e intereses para recibir mejores sugerencias.
            </p>
          )}
          <div>
            <p className="label">Proyectos que buscan un perfil como el tuyo</p>
            <ListaSugerencias items={datos.proyectos} vacio="Sin coincidencias por ahora." />
          </div>
          <div>
            <p className="label">Oportunidades para tus proyectos</p>
            <ListaSugerencias items={datos.oportunidades} vacio="Cuando participes en proyectos verás convocatorias afines." />
          </div>
          <NotaMetodo metodo={datos.metodo} />
        </div>
      )}
    </section>
  )
}
