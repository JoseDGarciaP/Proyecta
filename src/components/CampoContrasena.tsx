import { useState } from 'react'
import { Check, Circle, Eye, EyeOff } from 'lucide-react'
import { CONTRASENA_MAX, requisitosContrasena } from '@/lib/contrasena'

interface Props {
  id?: string
  etiqueta?: string
  valor: string
  alCambiar: (valor: string) => void
  autoComplete: 'current-password' | 'new-password'
  minLength?: number
  /** Enlace u otro elemento junto a la etiqueta (p. ej. «¿Olvidaste tu contraseña?»). */
  extra?: React.ReactNode
  /** Contraseña nueva: muestra la lista de requisitos que se marca mientras se escribe. */
  requisitos?: boolean
}

/** Campo de contraseña con botón para mostrarla y aviso cuando Bloq Mayús está activo. */
export function CampoContrasena({ id = 'password', etiqueta = 'Contraseña', valor, alCambiar, autoComplete, minLength, extra, requisitos }: Props) {
  const [visible, setVisible] = useState(false)
  const [mayusculas, setMayusculas] = useState(false)
  const revisarMayusculas = (e: React.KeyboardEvent) => setMayusculas(e.getModifierState('CapsLock'))

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label className="label" htmlFor={id}>{etiqueta}</label>
        {extra}
      </div>
      <div className="relative">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          required
          minLength={minLength}
          maxLength={requisitos ? CONTRASENA_MAX : undefined}
          autoComplete={autoComplete}
          autoCapitalize="none"
          spellCheck={false}
          className="input pr-10"
          aria-describedby={[mayusculas && `${id}-mayus`, requisitos && `${id}-requisitos`].filter(Boolean).join(' ') || undefined}
          value={valor}
          onChange={(e) => alCambiar(e.target.value)}
          onKeyDown={revisarMayusculas}
          onKeyUp={revisarMayusculas}
          onBlur={() => setMayusculas(false)}
        />
        <button
          type="button"
          className="absolute inset-y-0 right-0 grid w-10 place-items-center rounded-r-lg text-slate-400 hover:text-slate-600 focus-visible:text-brand-600 focus-visible:outline-none dark:hover:text-slate-200"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          aria-pressed={visible}
          aria-controls={id}
        >
          {visible ? <EyeOff size={16} aria-hidden /> : <Eye size={16} aria-hidden />}
        </button>
      </div>
      {mayusculas && (
        <p id={`${id}-mayus`} className="mt-1.5 text-sm text-amber-700 dark:text-amber-400">
          Bloq Mayús está activado.
        </p>
      )}
      {requisitos && (
        <ul id={`${id}-requisitos`} className="mt-2 grid gap-1 text-xs sm:grid-cols-2" aria-label="Requisitos de la contraseña">
          {requisitosContrasena(valor).map((r) => (
            <li key={r.texto} className={`flex items-center gap-1.5 ${r.cumple ? 'text-emerald-700 dark:text-emerald-400' : 'text-slate-500 dark:text-slate-400'}`}>
              {r.cumple ? <Check size={13} aria-hidden /> : <Circle size={11} aria-hidden />}
              <span>{r.texto}</span>
              <span className="sr-only">{r.cumple ? '(cumple)' : '(falta)'}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
