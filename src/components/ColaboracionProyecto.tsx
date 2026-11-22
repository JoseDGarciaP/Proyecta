import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Handshake, Mail, MessageCircle, UserPlus, Users, X } from 'lucide-react'
import {
  cambiarRolMiembro,
  cancelarInvitacionCorreo,
  colaboradoresSugeridos,
  invitar,
  invitarPorCorreo,
  listarInvitacionesCorreo,
  listarMiembros,
  misSolicitudes,
  proyectosSimilares,
  retirarMiembro,
  solicitarUnion,
  transferirProyecto,
} from '@/lib/colaboracion'
import { aceptarRecomendacion, anularRecomendacion } from '@/lib/ai'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import type { InvitacionCorreo, Miembro, Proyecto, Recomendacion, RespuestaSugerencias, Solicitud, Sugerencia } from '@/lib/types'
import { revisarCorreo } from '@/lib/correo'
import { useDominiosPermitidos } from '@/lib/parametros'
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
  const gestiona = esResponsable || puede('proyectos.moderar')
  const recargar = () => listarMiembros(proyecto.id).then(setMiembros).catch(() => {})
  const fallo = (e: unknown) => window.alert(e instanceof Error ? e.message : 'No se pudo completar')

  async function cambiarRol(m: Miembro) {
    const rol = window.prompt(`Nuevo rol de ${m.nombre}:`, m.rol)?.trim()
    if (!rol || rol === m.rol) return
    await cambiarRolMiembro(proyecto.id, m.usuario_id, rol).then(recargar).catch(fallo)
  }

  async function retirar(m: Miembro) {
    const yoMismo = m.usuario_id === usuario?.id
    const motivo = window.prompt(yoMismo ? '¿Por qué sales del proyecto?' : `Motivo para retirar a ${m.nombre} (se le avisará):`)?.trim()
    if (!motivo) return
    await retirarMiembro(proyecto.id, m.usuario_id, motivo)
      .then(() => (yoMismo ? window.location.reload() : recargar()))
      .catch(fallo)
  }

  async function transferir(m: Miembro) {
    if (!window.confirm(`¿Pasar la responsabilidad del proyecto a ${m.nombre}? Tú quedarás como colaborador/a.`)) return
    await transferirProyecto(proyecto.id, m.usuario_id).then(() => window.location.reload()).catch(fallo)
  }

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
              {(gestiona || m.usuario_id === usuario?.id) && (
                <p className="mt-1 flex flex-wrap gap-3 text-xs">
                  {gestiona && <button type="button" className="text-brand-700 hover:underline dark:text-brand-300" onClick={() => cambiarRol(m)}>Cambiar rol</button>}
                  {esResponsable && <button type="button" className="text-brand-700 hover:underline dark:text-brand-300" onClick={() => transferir(m)}>Hacer responsable</button>}
                  <button type="button" className="text-red-600 hover:underline" onClick={() => retirar(m)}>
                    {m.usuario_id === usuario?.id ? 'Salir del proyecto' : 'Retirar'}
                  </button>
                </p>
              )}
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
          <div className="space-y-3">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Eres responsable de este proyecto. Las solicitudes llegan a <Link to="/perfil" className="underline">tu perfil</Link>.
            </p>
            {puede('colaboracion.invitar') && <InvitarPorCorreo proyecto={proyecto} />}
          </div>
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

/**
 * Para quien registró el proyecto: invitar a alguien escribiendo su correo (institucional o, si es
 * aliado externo, el personal). Si ya tiene cuenta recibe una invitación normal; si no, le llega un
 * correo con un enlace para aceptar y crear su cuenta, y al registrarse queda en el equipo.
 */
function InvitarPorCorreo({ proyecto }: { proyecto: Proyecto }) {
  const [abierto, setAbierto] = useState(false)
  const [email, setEmail] = useState('')
  const [errorCorreo, setErrorCorreo] = useState('')
  const [aviso, setAviso] = useState('')
  const [pendientes, setPendientes] = useState<InvitacionCorreo[]>([])
  const dominios = useDominiosPermitidos()

  useEffect(() => {
    listarInvitacionesCorreo(proyecto.id).then(setPendientes).catch(() => setPendientes([]))
  }, [proyecto.id])

  const enviar = async (reco: Recomendacion) => {
    const revision = revisarCorreo(email)
    if (revision.error) {
      setErrorCorreo(email.trim() ? revision.error : 'Escribe el correo de la persona.')
      throw new Error('Revisa el correo de la persona.')
    }
    const res = await invitarPorCorreo(proyecto.id, revision.normalizado, reco)
    if (res.modo === 'usuario') {
      setAviso(`${res.solicitud?.usuario_nombre ?? revision.normalizado} ya tenía cuenta: le llegó la invitación a su perfil y a su correo.`)
    } else {
      setAviso(`Enviamos la invitación a ${revision.normalizado}. Cuando cree su cuenta y acepte, aparecerá en el equipo.`)
      if (res.invitacion) setPendientes((xs) => [res.invitacion!, ...xs.filter((x) => x.email !== res.invitacion!.email)])
    }
    setAbierto(false)
    setEmail('')
  }

  const cancelar = async (inv: InvitacionCorreo) => {
    await cancelarInvitacionCorreo(inv.id)
    setPendientes((xs) => xs.filter((x) => x.id !== inv.id))
  }

  return (
    <div className="space-y-3">
      <button className="btn-ghost w-full justify-center text-sm" onClick={() => { setAviso(''); setAbierto(true) }}>
        <Mail size={15} aria-hidden /> Invitar por correo
      </button>
      {aviso && <p className="text-xs text-emerald-700 dark:text-emerald-400" role="status">{aviso}</p>}
      {pendientes.length > 0 && (
        <div>
          <p className="text-xs font-medium text-slate-600 dark:text-slate-300">Invitaciones por correo sin registrarse</p>
          <ul className="mt-1.5 space-y-1.5">
            {pendientes.map((inv) => (
              <li key={inv.id} className="flex items-start justify-between gap-2 text-xs">
                <span className="min-w-0">
                  <span className="block truncate text-slate-800 dark:text-slate-200">{inv.email}</span>
                  <span className={inv.vencida ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500 dark:text-slate-400'}>
                    {inv.vencida ? 'Venció sin respuesta' : inv.estado === 'aceptada' ? 'Aceptó · falta que cree su cuenta' : 'Esperando respuesta'}
                    {' · '}{inv.rol_propuesto}
                  </span>
                </span>
                <button className="shrink-0 rounded p-1 text-slate-400 hover:text-rose-600" title="Retirar invitación"
                  aria-label={`Retirar la invitación a ${inv.email}`} onClick={() => cancelar(inv)}>
                  <X size={14} aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {abierto && (
        <Modal
          titulo="Invitar por correo"
          descripcion={<>Al proyecto «{proyecto.titulo}». Si la persona aún no está registrada, le llegará un correo para aceptar y crear su cuenta; al registrarse quedará en el equipo.</>}
          alCerrar={() => setAbierto(false)}
        >
          <div className="mb-3">
            <label className="label" htmlFor="invitar-correo">Correo de la persona</label>
            <input id="invitar-correo" type="email" required className="input" inputMode="email" autoCapitalize="none"
              spellCheck={false} placeholder={`nombre@${dominios[0] ?? "correo.edu.co"}`} value={email} aria-invalid={Boolean(errorCorreo)}
              onChange={(e) => { setEmail(e.target.value); setErrorCorreo('') }}
              onBlur={() => email.trim() && setErrorCorreo(revisarCorreo(email).error ?? '')} />
            {errorCorreo ? (
              <p className="mt-1.5 text-sm text-amber-700 dark:text-amber-400">
                {errorCorreo}
                {revisarCorreo(email).sugerencia && (
                  <button type="button" className="ml-2 font-medium text-brand-700 underline dark:text-brand-400"
                    onClick={() => { setEmail(revisarCorreo(email).sugerencia!); setErrorCorreo('') }}>Usar este</button>
                )}
              </p>
            ) : (
              <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">Su correo institucional; si es un aliado externo, puede ser el personal.</p>
            )}
          </div>
          <FormularioRecomendacion modo="invitacion" alEnviar={enviar} alCancelar={() => setAbierto(false)} />
        </Modal>
      )}
    </div>
  )
}

/** Proyectos parecidos y, para quien lo registró, personas que encajan con sus necesidades. */
export function RedProyecto({ proyecto }: { proyecto: Proyecto }) {
  const { usuario } = useSesion()
  const [similares, setSimilares] = useState<RespuestaSugerencias | null>(null)
  const [colaboradores, setColaboradores] = useState<RespuestaSugerencias | null>(null)
  const [invitados, setInvitados] = useState<Record<string, string>>({})
  const [invitando, setInvitando] = useState<Sugerencia | null>(null)
  const [peso, setPeso] = useState(0.3)
  const puede = usePuede()
  const esResponsable = Boolean(usuario && usuario.id === proyecto.creado_por) && puede('colaboracion.invitar')

  useEffect(() => {
    if (!apiHabilitada) return
    proyectosSimilares(proyecto.id).then(setSimilares).catch(() => setSimilares(null))
  }, [proyecto.id])

  useEffect(() => {
    if (!apiHabilitada || !esResponsable) return
    colaboradoresSugeridos(proyecto.id, peso).then(setColaboradores).catch(() => setColaboradores(null))
  }, [proyecto.id, esResponsable, peso])

  const marcar = (s: Sugerencia, estado: 'aceptada' | 'anulada') =>
    setColaboradores((c) => c && ({
      ...c,
      resultados: estado === 'anulada' ? c.resultados.filter((x) => x.id !== s.id) : c.resultados.map((x) => (x.id === s.id ? { ...x, estado } : x)),
    }))

  async function descartar(s: Sugerencia) {
    if (!s.recomendacion_id) return
    const motivo = window.prompt(`¿Por qué descartas a ${s.titulo}? No se volverá a sugerir.`)?.trim()
    if (!motivo || motivo.length < 5) return
    await anularRecomendacion(s.recomendacion_id, motivo).then(() => marcar(s, 'anulada')).catch(() => {})
  }

  if (!apiHabilitada) return null

  const invitarA = async (s: Sugerencia, reco: Recomendacion) => {
    await invitar(proyecto.id, s.id, reco)
    if (s.recomendacion_id && s.estado === 'pendiente') await aceptarRecomendacion(s.recomendacion_id).catch(() => {})
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
          <label className="mb-3 block text-xs text-slate-600 dark:text-slate-400">
            Peso de las habilidades pedidas frente al perfil completo: <b>{Math.round(peso * 100)} %</b>
            <input type="range" min={0} max={1} step={0.1} value={peso} onChange={(e) => setPeso(Number(e.target.value))} className="mt-1 w-full" />
          </label>
          {colaboradores ? (
            <ListaSugerencias
              items={colaboradores.resultados}
              vacio="Nadie encaja todavía. Describe mejor lo que necesita el proyecto o espera a que más personas completen su perfil."
              accion={(s) =>
                invitados[s.id] ? (
                  <span className="text-xs text-slate-500">{invitados[s.id]}</span>
                ) : (
                  <span className="flex gap-1">
                    <button className="btn-ghost text-xs" onClick={() => setInvitando(s)}>
                      <UserPlus size={14} aria-hidden /> Invitar
                    </button>
                    {s.recomendacion_id && s.estado === 'pendiente' && (
                      <button className="btn-ghost text-xs" title="No volver a sugerir" onClick={() => descartar(s)}>
                        <X size={14} aria-hidden /> Descartar
                      </button>
                    )}
                  </span>
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
