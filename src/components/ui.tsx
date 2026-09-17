import type { ReactNode } from 'react'
import { ESTADO_CLASS, ESTADO_LABEL, type Estado } from '@/lib/types'

export function Badge({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${className}`}>
      {children}
    </span>
  )
}

export function EstadoBadge({ estado }: { estado: Estado }) {
  return <Badge className={ESTADO_CLASS[estado]}>{ESTADO_LABEL[estado]}</Badge>
}

export function Progress({ valor }: { valor: number }) {
  return (
    <div
      className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
      role="progressbar"
      aria-valuenow={valor}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full rounded-full bg-linear-to-r from-brand-600 to-accent-500 transition-[width] duration-500 dark:from-brand-400 dark:to-accent-400"
        style={{ width: `${Math.min(100, Math.max(0, valor))}%` }}
      />
    </div>
  )
}

export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-slate-200 dark:bg-slate-800 ${className}`} />
}

export function EmptyState({ titulo, detalle, accion }: { titulo: string; detalle: string; accion?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center gap-2 px-6 py-14 text-center">
      <p className="font-medium text-slate-700 dark:text-slate-200">{titulo}</p>
      <p className="max-w-sm text-sm text-slate-500 dark:text-slate-400">{detalle}</p>
      {accion}
    </div>
  )
}

export function SectionTitle({ children, extra }: { children: ReactNode; extra?: ReactNode }) {
  return (
    <div className="mb-3 flex items-baseline justify-between gap-4">
      <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase dark:text-slate-400">{children}</h2>
      {extra}
    </div>
  )
}
