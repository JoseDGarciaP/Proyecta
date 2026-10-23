import { Monitor, Moon, Sun, type LucideIcon } from 'lucide-react'
import type { PreferenciaTema } from '@/hooks/useTheme'

const OPCIONES: { valor: PreferenciaTema; etiqueta: string; icono: LucideIcon }[] = [
  { valor: 'light', etiqueta: 'Claro', icono: Sun },
  { valor: 'dark', etiqueta: 'Oscuro', icono: Moon },
  { valor: 'system', etiqueta: 'Según el sistema', icono: Monitor },
]

interface Props {
  valor: PreferenciaTema
  onCambio: (p: PreferenciaTema) => void
}

/** Control de tres posiciones: claro, oscuro o el que use el equipo de la persona. */
export function SelectorTema({ valor, onCambio }: Props) {
  return (
    <div
      role="radiogroup"
      aria-label="Apariencia"
      className="inline-flex items-center rounded-md border border-slate-200 bg-white p-0.5 dark:border-slate-700 dark:bg-slate-900"
    >
      {OPCIONES.map(({ valor: v, etiqueta, icono: Icono }) => {
        const activo = v === valor
        return (
          <button
            key={v}
            type="button"
            role="radio"
            aria-checked={activo}
            aria-label={etiqueta}
            title={etiqueta}
            onClick={() => onCambio(v)}
            className={`grid h-7 w-7 place-items-center rounded transition focus-visible:ring-2 focus-visible:ring-brand-500/40 focus-visible:outline-none ${
              activo
                ? 'bg-brand-50 text-brand-700 dark:bg-brand-300/15 dark:text-brand-200'
                : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100'
            }`}
          >
            <Icono size={15} aria-hidden />
          </button>
        )
      })}
    </div>
  )
}
