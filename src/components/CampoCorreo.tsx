import { useState } from 'react'
import { revisarCorreo } from '@/lib/correo'

interface Props {
  valor: string
  alCambiar: (valor: string) => void
  institucional?: boolean
  /** Dominios institucionales aceptados (por defecto @ufpso.edu.co). */
  dominios?: string[]
  autoComplete?: string
  /** Texto de ayuda bajo el campo cuando no hay error. */
  ayuda?: string
  /** Muestra el error aunque la persona no haya salido del campo (al intentar enviar). */
  forzarRevision?: boolean
}

/** Campo de correo que revisa formato y errores de tipeo al salir del campo, y ofrece la corrección. */
export function CampoCorreo({ valor, alCambiar, institucional, dominios, autoComplete = 'email', forzarRevision, ayuda }: Props) {
  const [tocado, setTocado] = useState(false)
  const revision = revisarCorreo(valor, { institucional, dominios })
  const mostrar = (tocado || forzarRevision) && valor.trim() !== '' && revision.error

  return (
    <div>
      <label className="label" htmlFor="email">Correo</label>
      <input
        id="email"
        type="email"
        required
        inputMode="email"
        autoComplete={autoComplete}
        autoCapitalize="none"
        spellCheck={false}
        className="input"
        aria-invalid={Boolean(mostrar)}
        aria-describedby={mostrar || ayuda ? 'email-ayuda' : undefined}
        value={valor}
        onChange={(e) => alCambiar(e.target.value)}
        onBlur={() => setTocado(true)}
      />
      {!mostrar && ayuda && <p id="email-ayuda" className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">{ayuda}</p>}
      {mostrar && (
        <p id="email-ayuda" className="mt-1.5 text-sm text-amber-700 dark:text-amber-400">
          {revision.error}
          {revision.sugerencia && (
            <button
              type="button"
              className="ml-2 font-medium text-brand-700 underline dark:text-brand-400"
              onClick={() => alCambiar(revision.sugerencia!)}
            >
              Usar este
            </button>
          )}
        </p>
      )}
    </div>
  )
}
