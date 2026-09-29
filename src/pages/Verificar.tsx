import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle2, Loader2, XCircle } from 'lucide-react'
import { useSesion } from '@/lib/sesion'

/** Destino del enlace del correo: confirma la cuenta e inicia sesión. */
export function Verificar() {
  const [params] = useSearchParams()
  const { verificarCorreo } = useSesion()
  const navegar = useNavigate()
  const [estado, setEstado] = useState<'verificando' | 'listo' | string>('verificando')
  const hecho = useRef(false)

  useEffect(() => {
    const token = params.get('token')
    if (hecho.current) return // StrictMode ejecuta el efecto dos veces en desarrollo
    hecho.current = true
    if (!token) {
      setEstado('El enlace está incompleto.')
      return
    }
    verificarCorreo(token)
      .then(() => {
        setEstado('listo')
        setTimeout(() => navegar('/perfil', { replace: true }), 1500)
      })
      .catch((e: Error) => setEstado(e.message))
  }, [params, verificarCorreo, navegar])

  return (
    <div className="card mx-auto max-w-md p-8 text-center">
      {estado === 'verificando' ? (
        <>
          <Loader2 size={32} className="mx-auto animate-spin text-brand-600" aria-hidden />
          <p className="mt-4 text-slate-700 dark:text-slate-300">Confirmando tu correo…</p>
        </>
      ) : estado === 'listo' ? (
        <>
          <CheckCircle2 size={36} className="mx-auto text-emerald-600" aria-hidden />
          <h1 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">¡Correo confirmado!</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Te llevamos a tu perfil para que lo completes.</p>
        </>
      ) : (
        <>
          <XCircle size={36} className="mx-auto text-rose-600" aria-hidden />
          <h1 className="mt-4 text-xl font-semibold text-slate-900 dark:text-white">No pudimos confirmar tu correo</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{estado}</p>
          <Link to="/ingresar" className="btn-primary mt-6">Ir a ingresar y pedir otro enlace</Link>
        </>
      )}
    </div>
  )
}
