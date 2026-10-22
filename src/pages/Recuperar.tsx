import { useState } from 'react'
import { Link } from 'react-router-dom'
import { KeyRound, Loader2, MailCheck } from 'lucide-react'
import { useSesion } from '@/lib/sesion'
import { CampoCorreo } from '@/components/CampoCorreo'
import { revisarCorreo } from '@/lib/correo'

/** Pide el enlace para elegir una contraseña nueva. */
export function Recuperar() {
  const { recuperarContrasena } = useSesion()
  const [email, setEmail] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [enviado, setEnviado] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [intento, setIntento] = useState(false)

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setIntento(true)
    const revision = revisarCorreo(email)
    if (revision.error) return
    setEnviando(true)
    setError(null)
    try {
      await recuperarContrasena(revision.normalizado)
      setEnviado(revision.normalizado)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo enviar el enlace. Intenta en un momento.')
    } finally {
      setEnviando(false)
    }
  }

  if (enviado) {
    return (
      <div className="mx-auto max-w-md space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Revisa tu correo</h1>
        <div className="rounded-lg border border-brand-200 bg-brand-50 p-4 text-sm dark:border-brand-500/30 dark:bg-brand-500/10">
          <p className="flex items-center gap-2 font-medium text-brand-900 dark:text-brand-100">
            <MailCheck size={16} aria-hidden /> Enlace enviado
          </p>
          <p className="mt-1 text-brand-900/80 dark:text-brand-100/80">
            Si hay una cuenta con <b>{enviado}</b>, te llegará un enlace para elegir una contraseña nueva. Vence en una hora
            y sirve una sola vez. Si no lo ves, revisa la carpeta de spam.
          </p>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          ¿Ya la recordaste? <Link to="/ingresar" className="font-medium text-brand-700 dark:text-brand-400">Volver a ingresar</Link>
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={enviar} className="mx-auto max-w-md space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Recuperar contraseña</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Escribe el correo de tu cuenta y te enviaremos un enlace para elegir una contraseña nueva.
        </p>
      </header>
      <section className="card space-y-4 p-6">
        <CampoCorreo valor={email} alCambiar={setEmail} forzarRevision={intento} />
        {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}
        <button type="submit" className="btn-primary w-full justify-center" disabled={enviando}>
          {enviando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <KeyRound size={15} aria-hidden />}
          Enviar enlace
        </button>
        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          <Link to="/ingresar" className="font-medium text-brand-700 dark:text-brand-400">Volver a ingresar</Link>
        </p>
      </section>
    </form>
  )
}
