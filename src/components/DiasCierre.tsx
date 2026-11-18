import { Clock } from 'lucide-react'
import { diasRestantes } from '@/lib/format'

/** Días que faltan para el cierre de una convocatoria (HU-04). */
export function diasParaCierre(o: { cierra_en: string; dias_restantes?: number }) {
  return o.dias_restantes ?? diasRestantes(o.cierra_en)
}

export function DiasCierre({ dias, className = '' }: { dias: number; className?: string }) {
  const [texto, color] =
    dias < 0
      ? ['Cerrada', 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400']
      : dias === 0
        ? ['Cierra hoy', 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300']
        : [
            `Faltan ${dias} ${dias === 1 ? 'día' : 'días'}`,
            dias <= 7
              ? 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300'
              : dias <= 30
                ? 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300'
                : 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
          ]
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium tabular-nums ${color} ${className}`}>
      <Clock size={12} aria-hidden /> {texto}
    </span>
  )
}
