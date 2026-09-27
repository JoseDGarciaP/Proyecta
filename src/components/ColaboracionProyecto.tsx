import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Handshake, Loader2, UserPlus, Users } from 'lucide-react'
import {
  colaboradoresSugeridos,
  invitar,
  listarMiembros,
  misSolicitudes,
  proyectosSimilares,
  solicitarUnion,
} from '@/lib/colaboracion'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import type { Miembro, Proyecto, RespuestaSugerencias } from '@/lib/types'
import { ListaSugerencias, NotaMetodo } from '@/components/Sugerencias'

/** Miembros del proyecto y botón para pedir unirse (solo con la API conectada). */
export function MiembrosProyecto({ proyecto }: { proyecto: Proyecto }) {
  const { usuario } = useSesion()
  const [miembros, setMiembros] = useState<Miembro[]>([])
  const [pendiente, setPendiente] = useState(false)
  const [abierto, setAbierto] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [estado, setEstado] = useState<'' | 'enviando' | 'enviada' | string>('')

  useEffect(() => {
    if (!apiHabilitada) return
    listarMiembros(proyecto.id).then(setMiembros).catch(() => setMiembros([]))
    if (usuario) {
      misSolicitudes()
        .then((ss) => setPendiente(ss.some((s) => s.proyecto_id === proyecto.id && s.estado === 'pendiente')))
        .catch(() => {})
    }
  }, [proyecto.id, usuario])

  if (!apiHabilitada) return null

  const esResponsable = usuario?.id === proyecto.creado_por
  const esMiembro = esResponsable || miembros.some((m) => m.usuario_id === usuario?.id)

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setEstado('enviando')
    try {
      await solicitarUnion(proyecto.id, mensaje)
      setEstado('enviada')
      setPendiente(true)
      setAbierto(false)
    } catch (err) {
      setEstado((err as Error).message)
    }
  }

  return (
    <section className="card p-6">
      <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
        <Users size={16} aria-hidden /> Colaboradores
      </h2>
      {miembros.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Aún no se han sumado colaboradores por la plataforma.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {miembros.map((m) => (
            <li key={m.usuario_id} className="text-sm">
              <p className="font-medium text-slate-800 dark:text-slate-200">{m.nombre}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">{m.programa ?? m.rol}</p>
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
        {!usuario ? (
          <Link to="/ingresar" className="text-sm text-brand-700 hover:underline dark:text-brand-300">
            Ingresa para solicitar unirte
          </Link>
        ) : esResponsable ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Eres responsable de este proyecto. Las solicitudes llegan a <Link to="/perfil" className="underline">tu perfil</Link>.
          </p>
        ) : esMiembro ? (
          <p className="text-sm text-emerald-700 dark:text-emerald-400">Haces parte de este proyecto.</p>
        ) : pendiente ? (
          <p className="text-sm text-amber-700 dark:text-amber-400">
            {estado === 'enviada' ? 'Solicitud enviada.' : 'Tienes una solicitud pendiente.'} Síguela en <Link to="/perfil" className="underline">tu perfil</Link>.
          </p>
        ) : abierto ? (
          <form onSubmit={enviar} className="space-y-2">
            <textarea
              className="input min-h-20"
              placeholder="Cuéntale al equipo qué puedes aportar"
              value={mensaje}
              onChange={(e) => setMensaje(e.target.value)}
            />
            <div className="flex gap-2">
              <button className="btn-primary" disabled={estado === 'enviando'}>
                {estado === 'enviando' && <Loader2 size={15} className="animate-spin" aria-hidden />} Enviar solicitud
              </button>
              <button type="button" className="btn-ghost" onClick={() => setAbierto(false)}>Cancelar</button>
            </div>
            {estado && !['enviando', 'enviada'].includes(estado) && <p className="text-sm text-rose-600">{estado}</p>}
          </form>
        ) : (
          <button className="btn-primary w-full justify-center" onClick={() => setAbierto(true)}>
            <Handshake size={15} aria-hidden /> Solicitar unirme
          </button>
        )}
      </div>
    </section>
  )
}

/** Proyectos parecidos y, para quien lo registró, personas que encajan con sus necesidades. */
export function RedProyecto({ proyecto }: { proyecto: Proyecto }) {
  const { usuario } = useSesion()
  const [similares, setSimilares] = useState<RespuestaSugerencias | null>(null)
  const [colaboradores, setColaboradores] = useState<RespuestaSugerencias | null>(null)
  const [invitados, setInvitados] = useState<Record<string, string>>({})
  const esResponsable = Boolean(usuario && usuario.id === proyecto.creado_por)

  useEffect(() => {
    if (!apiHabilitada) return
    proyectosSimilares(proyecto.id).then(setSimilares).catch(() => setSimilares(null))
  }, [proyecto.id])

  useEffect(() => {
    if (!apiHabilitada || !esResponsable) return
    colaboradoresSugeridos(proyecto.id).then(setColaboradores).catch(() => setColaboradores(null))
  }, [proyecto.id, esResponsable])

  if (!apiHabilitada) return null

  const invitarA = async (usuarioId: string) => {
    setInvitados((x) => ({ ...x, [usuarioId]: 'Enviando…' }))
    try {
      await invitar(proyecto.id, usuarioId)
      setInvitados((x) => ({ ...x, [usuarioId]: 'Invitación enviada' }))
    } catch (e) {
      setInvitados((x) => ({ ...x, [usuarioId]: (e as Error).message }))
    }
  }

  return (
    <div className={`grid gap-4 ${esResponsable ? 'lg:grid-cols-2' : ''}`}>
      <section className="card p-5">
        <h2 className="font-semibold text-slate-900 dark:text-white">Proyectos similares</h2>
        <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">Para articularse con equipos que trabajan en lo mismo o evitar duplicar esfuerzos.</p>
        {similares ? (
          <>
            <ListaSugerencias items={similares.resultados} vacio="No hay proyectos parecidos registrados." />
            <NotaMetodo metodo={similares.metodo} />
          </>
        ) : (
          <p className="text-sm text-slate-500">Buscando…</p>
        )}
      </section>

      {esResponsable && (
        <section className="card p-5">
          <h2 className="font-semibold text-slate-900 dark:text-white">Posibles colaboradores</h2>
          <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
            Personas cuyo perfil encaja con «Lo que necesita». Solo lo ves tú, como responsable.
          </p>
          {colaboradores ? (
            <ListaSugerencias
              items={colaboradores.resultados}
              vacio="Nadie encaja todavía. Describe mejor lo que necesita el proyecto o espera a que más personas completen su perfil."
              accion={(s) =>
                invitados[s.id] ? (
                  <span className="text-xs text-slate-500">{invitados[s.id]}</span>
                ) : (
                  <button className="btn-ghost text-xs" onClick={() => invitarA(s.id)}>
                    <UserPlus size={14} aria-hidden /> Invitar
                  </button>
                )
              }
            />
          ) : (
            <p className="text-sm text-slate-500">Buscando…</p>
          )}
        </section>
      )}
    </div>
  )
}
