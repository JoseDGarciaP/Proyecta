import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Handshake, MessageCircle, UserPlus, Users } from 'lucide-react'
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
import type { Miembro, Proyecto, Recomendacion, RespuestaSugerencias, Solicitud, Sugerencia } from '@/lib/types'
import { ListaSugerencias, NotaMetodo } from '@/components/Sugerencias'
import { ChatSolicitud } from '@/components/ChatSolicitud'
import { FormularioRecomendacion } from '@/components/FormularioRecomendacion'
import { Modal } from '@/components/Modal'
import { NombrePersona } from '@/components/Insignia'
import { usePuede } from '@/lib/permisos'

/** Miembros del proyecto y botón para pedir unirse (solo con la API conectada). */
export function MiembrosProyecto({ proyecto }: { proyecto: Proyecto }) {
  const { usuario } = useSesion()
  const puede = usePuede()
  const [miembros, setMiembros] = useState<Miembro[]>([])
  const [pendiente, setPendiente] = useState<Solicitud | null>(null)
  const [conversando, setConversando] = useState(false)
  const [abierto, setAbierto] = useState(false)
  const [enviada, setEnviada] = useState(false)

  useEffect(() => {
    if (!apiHabilitada) return
    listarMiembros(proyecto.id).then(setMiembros).catch(() => setMiembros([]))
    if (usuario) {
      misSolicitudes()
        .then((ss) => setPendiente(ss.find((s) => s.proyecto_id === proyecto.id && s.estado === 'pendiente') ?? null))
        .catch(() => {})
    }
  }, [proyecto.id, usuario])

  if (!apiHabilitada) return null

  const esResponsable = usuario?.id === proyecto.creado_por
  const esMiembro = esResponsable || miembros.some((m) => m.usuario_id === usuario?.id)

  const enviar = async (reco: Recomendacion) => {
    setPendiente(await solicitarUnion(proyecto.id, reco))
    setEnviada(true)
    setConversando(true) // queda abierta por si el responsable responde con preguntas
    setAbierto(false)
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
              <p className="font-medium text-slate-800 dark:text-slate-200"><NombrePersona id={m.usuario_id} nombre={m.nombre} /></p>
              <p className="text-xs text-slate-500 dark:text-slate-400">{m.rol}{m.programa && ` · ${m.programa}`}</p>
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
          <div className="space-y-3">
            <p className="text-sm text-amber-700 dark:text-amber-400">
              {enviada ? 'Solicitud enviada: le avisamos al responsable.' : pendiente.tipo === 'invitacion' ? 'Te invitaron a este proyecto.' : 'Tienes una solicitud pendiente.'}{' '}
              Síguela en <Link to="/perfil" className="underline">tu perfil</Link>.
            </p>
            <button className="btn-ghost w-full justify-center text-sm" onClick={() => setConversando((x) => !x)} aria-expanded={conversando}>
              <MessageCircle size={15} aria-hidden /> {conversando ? 'Ocultar conversación' : 'Conversar con el responsable'}
            </button>
            {conversando && <ChatSolicitud solicitud={pendiente} />}
          </div>
        ) : puede('colaboracion.solicitar') ? (
          <button className="btn-primary w-full justify-center" onClick={() => setAbierto(true)}>
            <Handshake size={15} aria-hidden /> Solicitar unirme
          </button>
        ) : (
          <p className="text-xs text-slate-500 dark:text-slate-400">Tu rol no tiene permiso para pedir unirse a proyectos.</p>
        )}
        {abierto && usuario && (
          <Modal
            titulo={`Solicitar unirme a «${proyecto.titulo}»`}
            descripcion="Todas las solicitudes llevan la misma información para que el responsable pueda decidir."
            alCerrar={() => setAbierto(false)}
          >
            {proyecto.necesidades && (
              <p className="mb-4 rounded-lg bg-accent-50 p-3 text-xs text-accent-800 dark:bg-accent-500/10 dark:text-accent-200">
                <b>Lo que necesita el proyecto:</b> {proyecto.necesidades}
              </p>
            )}
            <FormularioRecomendacion
              modo="solicitud"
              inicial={{ habilidades: usuario.habilidades }}
              alEnviar={enviar}
              alCancelar={() => setAbierto(false)}
            />
          </Modal>
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
  const [invitando, setInvitando] = useState<Sugerencia | null>(null)
  const puede = usePuede()
  const esResponsable = Boolean(usuario && usuario.id === proyecto.creado_por) && puede('colaboracion.invitar')

  useEffect(() => {
    if (!apiHabilitada) return
    proyectosSimilares(proyecto.id).then(setSimilares).catch(() => setSimilares(null))
  }, [proyecto.id])

  useEffect(() => {
    if (!apiHabilitada || !esResponsable) return
    colaboradoresSugeridos(proyecto.id).then(setColaboradores).catch(() => setColaboradores(null))
  }, [proyecto.id, esResponsable])

  if (!apiHabilitada) return null

  const invitarA = async (s: Sugerencia, reco: Recomendacion) => {
    await invitar(proyecto.id, s.id, reco)
    setInvitados((x) => ({ ...x, [s.id]: 'Invitación enviada' }))
    setInvitando(null)
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
                  <button className="btn-ghost text-xs" onClick={() => setInvitando(s)}>
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
      {invitando && (
        <Modal
          titulo={`Invitar a ${invitando.titulo}`}
          descripcion={`Al proyecto «${proyecto.titulo}». Le llegará un aviso en la plataforma y por correo.`}
          alCerrar={() => setInvitando(null)}
        >
          <FormularioRecomendacion
            modo="invitacion"
            inicial={{ motivacion: invitando.razon }}
            alEnviar={(reco) => invitarA(invitando, reco)}
            alCancelar={() => setInvitando(null)}
          />
        </Modal>
      )}
    </div>
  )
}
