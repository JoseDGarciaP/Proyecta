import { useState } from 'react'
import { MailCheck } from 'lucide-react'
import { useSesion } from '@/lib/sesion'

/** Indica que falta confirmar el correo y permite pedir otro enlace. */
export function AvisoVerificacion({ email, titulo }: { email: string; titulo: string }) {
  const { reenviarVerificacion } = useSesion()
  const [estado, setEstado] = useState<'' | 'enviando' | 'enviado' | 'error'>('')

  const reenviar = async () => {
    setEstado('enviando')
    try {
      await reenviarVerificacion(email)
      setEstado('enviado')
    } catch {
      setEstado('error')
    }
  }

  return (
    <div className="rounded-lg border border-brand-200 bg-brand-50 p-4 text-sm dark:border-brand-500/30 dark:bg-brand-500/10">
      <p className="flex items-center gap-2 font-medium text-brand-900 dark:text-brand-100">
        <MailCheck size={16} aria-hidden /> {titulo}
      </p>
      <p className="mt-1 text-brand-900/80 dark:text-brand-100/80">
        Enviamos un enlace a <b>{email}</b>. Ábrelo para activar tu cuenta. Si no lo ves, revisa la carpeta de spam.
      </p>
      <button type="button" className="mt-3 text-sm font-medium text-brand-700 underline disabled:opacity-60 dark:text-brand-300" onClick={reenviar} disabled={estado === 'enviando'}>
        {estado === 'enviado' ? 'Listo, te enviamos otro enlace' : estado === 'enviando' ? 'Enviando…' : 'Enviar el enlace de nuevo'}
      </button>
      {estado === 'error' && <p className="mt-1 text-rose-600">No se pudo enviar. Intenta en un momento.</p>}
    </div>
  )
}
