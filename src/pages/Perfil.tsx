import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, Handshake, Loader2, Send, Sparkles, UserRound, X } from 'lucide-react'
import {
  actualizarPerfil,
  listaATexto,
  obtenerPerfil,
  responderSolicitud,
  sugerenciasParaMi,
  textoALista,
} from '@/lib/colaboracion'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import type { Perfil as DatosPerfil, Solicitud, SugerenciasParaMi } from '@/lib/types'
import { Badge, EmptyState, EstadoBadge, SectionTitle, Skeleton } from '@/components/ui'
import { ListaSugerencias, NotaMetodo } from '@/components/Sugerencias'
import { formatDate } from '@/lib/format'

const ESTADO_SOLICITUD: Record<Solicitud['estado'], string> = {
  pendiente: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  aceptada: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  rechazada: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
  cancelada: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
}

export function Perfil() {
  const [perfil, setPerfil] = useState<DatosPerfil | null>(null)
  const [error, setError] = useState('')

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
        <span className="grid h-14 w-14 place-items-center rounded-full bg-linear-to-br from-brand-600 to-accent-500 text-lg font-semibold text-white">
          {iniciales}
        </span>
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{usuario.nombre}</h1>
          <p className="text-sm text-slate-500 capitalize dark:text-slate-400">
            {usuario.rol}
            {usuario.programa && ` · ${usuario.programa}`} · <span className="normal-case">{usuario.email}</span>
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
        <div className="space-y-6 lg:col-span-2">
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

          <Alianzas alianzas={perfil.alianzas} alCambiar={cargar} />
        </div>

        <div className="space-y-6">
          <EditarPerfil perfil={perfil} alGuardar={cargar} />
          <ParaMi version={usuario} />
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

function Alianzas({ alianzas, alCambiar }: { alianzas: Solicitud[]; alCambiar: () => void }) {
  const [ocupado, setOcupado] = useState<string | null>(null)
  const [error, setError] = useState('')
  const porResponder = alianzas.filter((a) => a.por_responder)
  const resto = alianzas.filter((a) => !a.por_responder)

  const actuar = async (s: Solicitud, accion: 'aceptar' | 'rechazar' | 'cancelar') => {
    setOcupado(s.id)
    setError('')
    try {
      await responderSolicitud(s.id, accion)
      alCambiar()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setOcupado(null)
    }
  }

  return (
    <section>
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
                <li key={s.id} className="card border-accent-300 p-4 dark:border-accent-500/40">
                  <p className="text-sm text-slate-800 dark:text-slate-200">
                    <Handshake size={15} className="mr-1.5 inline text-accent-600" aria-hidden />
                    {s.tipo === 'solicitud' ? (
                      <><b>{s.usuario_nombre}</b> quiere unirse a <Link className="font-medium hover:underline" to={`/proyectos/${s.proyecto_id}`}>{s.proyecto_titulo}</Link></>
                    ) : (
                      <>Te invitaron a <Link className="font-medium hover:underline" to={`/proyectos/${s.proyecto_id}`}>{s.proyecto_titulo}</Link></>
                    )}
                  </p>
                  {s.mensaje && <p className="mt-1 text-sm text-slate-600 italic dark:text-slate-400">«{s.mensaje}»</p>}
                  <div className="mt-3 flex gap-2">
                    <button className="btn-primary" disabled={ocupado === s.id} onClick={() => actuar(s, 'aceptar')}>
                      <Check size={15} aria-hidden /> Aceptar
                    </button>
                    <button className="btn-ghost" disabled={ocupado === s.id} onClick={() => actuar(s, 'rechazar')}>
                      <X size={15} aria-hidden /> Rechazar
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {resto.length > 0 && (
            <ul className="card divide-y divide-slate-200 dark:divide-slate-800">
              {resto.map((s) => (
                <li key={s.id} className="flex flex-wrap items-center gap-3 px-5 py-3 text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="text-slate-800 dark:text-slate-200">
                      {s.tipo === 'solicitud' ? `Solicitud de ${s.usuario_nombre}` : `Invitación a ${s.usuario_nombre}`} ·{' '}
                      <Link className="font-medium hover:underline" to={`/proyectos/${s.proyecto_id}`}>{s.proyecto_titulo}</Link>
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {formatDate(s.creado_en)}
                      {s.respuesta && ` · «${s.respuesta}»`}
                    </p>
                  </div>
                  <Badge className={ESTADO_SOLICITUD[s.estado]}>{s.estado}</Badge>
                  {s.estado === 'pendiente' && (
                    <button className="btn-ghost text-xs" disabled={ocupado === s.id} onClick={() => actuar(s, 'cancelar')}>
                      Cancelar
                    </button>
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
