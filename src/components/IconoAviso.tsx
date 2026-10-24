import { Award, Ban, Bell, CheckCircle2, ClipboardCheck, FileBadge, Handshake, Mail, MessageSquare, Send, ShieldAlert, TrendingUp, UserCog, XCircle } from 'lucide-react'
import type { TipoNotificacion } from '@/lib/types'

const ICONOS: Record<TipoNotificacion, { Icono: typeof Bell; clase: string }> = {
  solicitud_nueva: { Icono: Handshake, clase: 'bg-accent-100 text-accent-700 dark:bg-accent-500/15 dark:text-accent-300' },
  invitacion_nueva: { Icono: Mail, clase: 'bg-accent-100 text-accent-700 dark:bg-accent-500/15 dark:text-accent-300' },
  solicitud_aceptada: { Icono: CheckCircle2, clase: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300' },
  solicitud_rechazada: { Icono: XCircle, clase: 'bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300' },
  solicitud_cancelada: { Icono: Ban, clase: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300' },
  mensajes_sin_leer: { Icono: MessageSquare, clase: 'bg-brand-100 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300' },
  cuenta: { Icono: UserCog, clase: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300' },
  insignia: { Icono: Award, clase: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300' },
  nivel: { Icono: TrendingUp, clase: 'bg-brand-100 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300' },
  evidencia: { Icono: FileBadge, clase: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300' },
  postulacion: { Icono: Send, clase: 'bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300' },
  revision: { Icono: ClipboardCheck, clase: 'bg-accent-100 text-accent-700 dark:bg-accent-500/15 dark:text-accent-300' },
  moderacion: { Icono: ShieldAlert, clase: 'bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300' },
}

export function IconoAviso({ tipo }: { tipo: TipoNotificacion }) {
  const { Icono, clase } = ICONOS[tipo] ?? { Icono: Bell, clase: 'bg-slate-100 text-slate-600' }
  return (
    <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full ${clase}`}>
      <Icono size={15} aria-hidden />
    </span>
  )
}

const relativo = new Intl.RelativeTimeFormat('es', { numeric: 'auto' })

/** «hace 5 minutos», «ayer»… */
export function hace(iso: string): string {
  const seg = (Date.parse(iso) - Date.now()) / 1000
  const pasos: [number, Intl.RelativeTimeFormatUnit][] = [[60, 'second'], [60, 'minute'], [24, 'hour'], [7, 'day'], [4.35, 'week'], [12, 'month']]
  let valor = seg
  for (const [tam, unidad] of pasos) {
    if (Math.abs(valor) < tam) return relativo.format(Math.round(valor), unidad)
    valor /= tam
  }
  return relativo.format(Math.round(valor), 'year')
}
