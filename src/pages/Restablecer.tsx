import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Loader2, Save, XCircle } from 'lucide-react'
import { useSesion } from '@/lib/sesion'
import { CampoContrasena } from '@/components/CampoContrasena'

/** Destino del enlace del correo: elige una contraseña nueva y deja la sesión iniciada. */
export function Restablecer() {
  const [params] = useSearchParams()
  const token = params.get('token')
  const { restablecerContrasena } = useSesion()
  const navegar = useNavigate()
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!token) {
    return (
      <div className="card mx-auto max-w-md p-8 text-center">
        <XCircle size={36} className="mx-auto text-rose-600" aria-hidden />
        <h1 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">El enlace está incompleto</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Ábrelo de nuevo desde el correo o pide otro.</p>
        <Link to="/recuperar" className="btn-primary mt-6">Pedir otro enlace</Link>
      </div>
    )
  }

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmacion) {
      setError('Las contraseñas no coinciden.')
      return
    }
    setEnviando(true)
    setError(null)
    try {
      await restablecerContrasena(token, password)
      navegar('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cambiar la contraseña.')
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="mx-auto max-w-md space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Elige una contraseña nueva</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Al guardarla entrarás directamente a Proyecta.</p>
      </header>
      <section className="card space-y-4 p-6">
        <CampoContrasena
          etiqueta="Contraseña nueva (mínimo 8 caracteres)"
          valor={password}
          alCambiar={setPassword}
          autoComplete="new-password"
          minLength={8}
        />
        <CampoContrasena
          id="confirmacion"
          etiqueta="Repite la contraseña"
          valor={confirmacion}
          alCambiar={setConfirmacion}
          autoComplete="new-password"
          minLength={8}
        />
        {error && (
          <p className="text-sm text-rose-600 dark:text-rose-400">
            {error}{' '}
            {error.includes('Pide uno nuevo') && (
              <Link to="/recuperar" className="font-medium text-brand-700 underline dark:text-brand-400">Pedir otro enlace</Link>
            )}
          </p>
        )}
        <button type="submit" className="btn-primary w-full justify-center" disabled={enviando}>
          {enviando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Save size={15} aria-hidden />}
          Guardar y entrar
        </button>
      </section>
    </form>
  )
}
