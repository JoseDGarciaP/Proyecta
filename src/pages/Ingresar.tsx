import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Loader2, LogIn } from 'lucide-react'
import { useSesion } from '@/lib/sesion'

export function Ingresar() {
  const { ingresar } = useSesion()
  const navegar = useNavigate()
  const destino = (useLocation().state as { desde?: string } | null)?.desde ?? '/'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      await ingresar(email.trim(), password)
      navegar(destino, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible ingresar.')
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="mx-auto max-w-md space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Ingresar</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Usa tu correo institucional de la UFPSO.</p>
      </header>
      <section className="card space-y-4 p-6">
        <div>
          <label className="label" htmlFor="email">Correo</label>
          <input id="email" type="email" required autoComplete="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="password">Contraseña</label>
          <input id="password" type="password" required autoComplete="current-password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}
        <button type="submit" className="btn-primary w-full justify-center" disabled={enviando}>
          {enviando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <LogIn size={15} aria-hidden />}
          Ingresar
        </button>
        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          ¿No tienes cuenta?{' '}
          <Link to="/registro" state={{ desde: destino }} className="font-medium text-brand-700 dark:text-brand-400">Regístrate</Link>
        </p>
      </section>
    </form>
  )
}
