import type { LucideIcon } from 'lucide-react'

interface Props {
  etiqueta: string
  valor: string
  detalle?: string
  icono: LucideIcon
  tendencia?: number
  /** 'azul' para métricas de volumen, 'fucsia' para las de intensidad o dinero. */
  tono?: 'azul' | 'fucsia'
}

const TONOS = {
  azul: 'bg-brand-50 text-brand-700 dark:bg-brand-500/12 dark:text-brand-300',
  fucsia: 'bg-accent-50 text-accent-700 dark:bg-accent-500/12 dark:text-accent-300',
} as const

export function StatCard({ etiqueta, valor, detalle, icono: Icono, tendencia, tono = 'azul' }: Props) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{etiqueta}</p>
        <span className={`rounded-lg p-2 ${TONOS[tono]}`}>
          <Icono size={16} aria-hidden />
        </span>
      </div>
      <p className="mt-3 text-2xl font-semibold tracking-tight text-slate-900 tabular-nums dark:text-white">{valor}</p>
      {(detalle || tendencia !== undefined) && (
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {tendencia !== undefined && (
            <span className={tendencia >= 0 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}>
              {tendencia >= 0 ? '▲' : '▼'} {Math.abs(tendencia)}%{' '}
            </span>
          )}
          {detalle}
        </p>
      )}
    </div>
  )
}
