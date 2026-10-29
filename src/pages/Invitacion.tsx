import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2, Handshake, Loader2, XCircle } from 'lucide-react'
import { responderInvitacion, verInvitacion } from '@/lib/colaboracion'
import { useSesion } from '@/lib/sesion'
import type { InvitacionPublica } from '@/lib/types'

/**
 * Destino del enlace que llega por correo a quien invitan a un proyecto sin tener cuenta.
 * Puede aceptar o rechazar sin registrarse; si acepta, sigue a crear la cuenta con ese correo
 * y al terminar queda en el equipo.
 */
export function Invitacion() {
  const [params] = useSearchParams()
  const codigo = params.get('token') ?? ''
  const { usuario } = useSesion()
  const navegar = useNavigate()
  const [inv, setInv] = useState<InvitacionPublica | null>(null)
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState<'aceptar' | 'rechazar' | null>(null)

  useEffect(() => {
    if (!codigo) {
      setError('El enlace está incompleto. Ábrelo de nuevo desde el correo.')
      return
    }
    verInvitacion(codigo).then(setInv).catch((e: Error) => setError(e.message))
  }, [codigo])

  const responder = async (accion: 'aceptar' | 'rechazar') => {
    setEnviando(accion)
    setError('')
    try {
      const nueva = await responderInvitacion(codigo, accion)
      setInv(nueva)
      // Sin cuenta todavía: a crearla con el correo de la invitación.
      if (accion === 'aceptar' && !nueva.cuenta_existe && !usuario) {
        navegar(`/registro?invitacion=${encodeURIComponent(codigo)}`, { state: { desde: `/proyectos/${nueva.proyecto_id}` } })
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setEnviando(null)
    }
  }

  if (!inv) {
    return (
      <div className="card mx-auto max-w-md p-8 text-center">
        {error ? (
          <>
            <XCircle size={36} className="mx-auto text-rose-600" aria-hidden />
            <h1 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">No pudimos abrir la invitación</h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{error}</p>
          </>
        ) : (
          <Loader2 size={32} className="mx-auto animate-spin text-brand-600" aria-label="Cargando invitación" />
        )}
      </div>
    )
  }

  const rutaProyecto = `/proyectos/${inv.proyecto_id}`
  const otraCuenta = usuario && usuario.email?.toLowerCase() !== inv.email
  const abierta = inv.estado === 'pendiente' && !inv.vencida

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <header>
        <p className="text-sm font-medium text-brand-700 dark:text-brand-400">Invitación a un proyecto</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{inv.proyecto_titulo}</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{inv.proyecto_resumen}</p>
      </header>

      <section className="card space-y-4 p-6">
        <p className="text-sm text-slate-700 dark:text-slate-300">
          <b>{inv.invitado_por}</b> invitó a <b>{inv.email}</b> a hacer parte del equipo.
        </p>
        <dl className="grid gap-3 text-sm sm:grid-cols-[9rem_1fr]">
          <dt className="text-slate-500 dark:text-slate-400">Rol propuesto</dt>
          <dd className="text-slate-900 dark:text-slate-100">{inv.rol_propuesto}</dd>
          <dt className="text-slate-500 dark:text-slate-400">Qué se espera</dt>
          <dd className="text-slate-900 dark:text-slate-100">{inv.aporte}</dd>
          {inv.disponibilidad_horas != null && (
            <>
              <dt className="text-slate-500 dark:text-slate-400">Dedicación</dt>
              <dd className="text-slate-900 dark:text-slate-100">{inv.disponibilidad_horas} horas por semana</dd>
            </>
          )}
          {inv.habilidades.length > 0 && (
            <>
              <dt className="text-slate-500 dark:text-slate-400">Habilidades</dt>
              <dd className="text-slate-900 dark:text-slate-100">{inv.habilidades.join(', ')}</dd>
            </>
          )}
          <dt className="text-slate-500 dark:text-slate-400">Por qué te invitan</dt>
          <dd className="text-slate-900 dark:text-slate-100">{inv.motivacion}</dd>
          {inv.mensaje && (
            <>
              <dt className="text-slate-500 dark:text-slate-400">Nota</dt>
              <dd className="text-slate-900 dark:text-slate-100">{inv.mensaje}</dd>
            </>
          )}
        </dl>

        <div className="border-t border-slate-200 pt-4 dark:border-slate-800">
          {inv.es_miembro ? (
            <Estado ok texto="Ya haces parte del equipo de este proyecto.">
              {usuario ? (
                <Link to={rutaProyecto} className="btn-primary">Ir al proyecto</Link>
              ) : (
                <Link to="/ingresar" state={{ desde: rutaProyecto }} className="btn-primary">Ingresar</Link>
              )}
            </Estado>
          ) : inv.estado === 'aceptada' ? (
            <Estado ok texto={`Aceptaste la invitación. Crea tu cuenta con ${inv.email} y quedarás en el equipo automáticamente.`}>
              {inv.cuenta_existe ? (
                <Link to="/ingresar" state={{ desde: rutaProyecto }} className="btn-primary">Ingresar</Link>
              ) : (
                <Link to={`/registro?invitacion=${encodeURIComponent(codigo)}`} state={{ desde: rutaProyecto }} className="btn-primary">Crear mi cuenta</Link>
              )}
            </Estado>
          ) : inv.estado === 'rechazada' ? (
            <Estado texto="Rechazaste esta invitación. Le avisamos al responsable." />
          ) : inv.estado === 'cancelada' ? (
            <Estado texto="El responsable retiró esta invitación." />
          ) : inv.vencida ? (
            <Estado texto="Esta invitación venció. Pide al responsable que te invite de nuevo." />
          ) : null}

          {abierta && (
            <div className="space-y-3">
              {otraCuenta && (
                <p className="rounded-lg bg-amber-50 p-3 text-xs text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
                  Ingresaste como {usuario.email}, pero la invitación es para {inv.email}. Al aceptar quedará para la cuenta de {inv.email}.
                </p>
              )}
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {inv.cuenta_existe
                  ? 'Ya tienes cuenta con este correo: al aceptar entras al equipo de una vez.'
                  : `Si aceptas, te pediremos crear tu cuenta con ${inv.email} y al terminar quedarás en el equipo.`}
              </p>
              <div className="flex flex-wrap gap-2">
                <button className="btn-primary" disabled={enviando !== null} onClick={() => responder('aceptar')}>
                  {enviando === 'aceptar' ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Handshake size={15} aria-hidden />}
                  Aceptar invitación
                </button>
                <button className="btn-ghost" disabled={enviando !== null} onClick={() => responder('rechazar')}>
                  {enviando === 'rechazar' && <Loader2 size={15} className="animate-spin" aria-hidden />} Rechazar
                </button>
              </div>
            </div>
          )}
          {error && <p className="mt-3 text-sm text-rose-600 dark:text-rose-400">{error}</p>}
        </div>
      </section>
    </div>
  )
}

function Estado({ ok, texto, children }: { ok?: boolean; texto: string; children?: React.ReactNode }) {
  return (
    <div className="space-y-3">
      <p className={`flex items-start gap-2 text-sm ${ok ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400'}`}>
        {ok ? <CheckCircle2 size={16} className="mt-0.5 shrink-0" aria-hidden /> : <XCircle size={16} className="mt-0.5 shrink-0" aria-hidden />}
        {texto}
      </p>
      {children}
    </div>
  )
}
