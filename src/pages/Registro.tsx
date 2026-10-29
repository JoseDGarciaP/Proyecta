import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Loader2, UserPlus } from 'lucide-react'
import { useSesion, type DatosRegistro } from '@/lib/sesion'
import type { Rol } from '@/lib/types'
import { BotonGoogle } from '@/components/BotonGoogle'
import { AvisoVerificacion } from '@/components/AvisoVerificacion'
import { CampoCorreo } from '@/components/CampoCorreo'
import { CampoContrasena } from '@/components/CampoContrasena'
import { revisarCorreo } from '@/lib/correo'
import { useDominiosPermitidos, useRolesRegistro } from '@/lib/parametros'
import { PROGRAMAS } from '@/lib/programas'

// Mientras cargan los roles configurados por el admin (o en modo demostración).
const ROLES_INICIALES = [
  { clave: 'estudiante', nombre: 'Estudiante', descripcion: '', institucional: true },
  { clave: 'docente', nombre: 'Docente', descripcion: '', institucional: true },
  { clave: 'administrativo', nombre: 'Administrativo', descripcion: '', institucional: true },
  { clave: 'aliado', nombre: 'Aliado externo', descripcion: '', institucional: false },
]

export function Registro() {
  const { registrar, ingresarConGoogle } = useSesion()
  const navegar = useNavigate()
  const destino = (useLocation().state as { desde?: string } | null)?.desde ?? '/'
  const [form, setForm] = useState<DatosRegistro>({ nombre: '', email: '', password: '', rol: 'estudiante', programa: '' })
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [registrado, setRegistrado] = useState(false)
  const [intento, setIntento] = useState(false)
  const [confirmacion, setConfirmacion] = useState('')
  const rolesApi = useRolesRegistro()
  const roles = rolesApi.length ? rolesApi : ROLES_INICIALES
  const rolElegido = roles.find((r) => r.clave === form.rol)
  const institucional = rolElegido?.institucional ?? true
  const dominios = useDominiosPermitidos()
  const listaDominios = dominios.map((d) => `@${d}`).join(' o ')

  const set = <K extends keyof DatosRegistro>(clave: K, valor: DatosRegistro[K]) => setForm((f) => ({ ...f, [clave]: valor }))

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setIntento(true)
    const revision = revisarCorreo(form.email, { institucional, dominios })
    if (revision.error) return
    if (form.password !== confirmacion) {
      setError('Las contraseñas no coinciden.')
      return
    }
    setEnviando(true)
    setError(null)
    try {
      await registrar({ ...form, nombre: form.nombre.trim(), email: revision.normalizado, programa: form.programa?.trim() || null })
      setRegistrado(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible crear la cuenta.')
      setEnviando(false)
    }
  }

  const conGoogle = async (credential: string) => {
    setError(null)
    try {
      await ingresarConGoogle(credential)
      navegar(destino, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible ingresar con Google.')
    }
  }

  if (registrado) {
    return (
      <div className="mx-auto max-w-md space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Revisa tu correo</h1>
        <AvisoVerificacion email={form.email.trim().toLowerCase()} titulo="Tu cuenta está casi lista" />
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Después de confirmar podrás <Link to="/ingresar" className="font-medium text-brand-700 dark:text-brand-400">ingresar</Link>.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={enviar} className="mx-auto max-w-md space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Crear cuenta</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Estudiantes, docentes y administrativos se registran con su correo institucional {listaDominios}; los aliados externos pueden usar su correo personal. Te enviaremos un enlace para confirmar que el correo es tuyo.
        </p>
      </header>
      <section className="card space-y-4 p-6">
        <BotonGoogle alIngresar={conGoogle} />
        <div>
          <label className="label" htmlFor="nombre">Nombre completo</label>
          <input id="nombre" required minLength={3} className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="rol">Soy</label>
          <select id="rol" className="input" value={form.rol} onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value as Rol, programa: '' }))}>
            {roles.map((r) => <option key={r.clave} value={r.clave}>{r.nombre}</option>)}
          </select>
          {rolElegido?.descripcion && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{rolElegido.descripcion}</p>}
        </div>
        <CampoCorreo valor={form.email} alCambiar={(v) => set('email', v)} institucional={institucional} dominios={dominios}
          forzarRevision={intento}
          ayuda={institucional ? `Usa tu correo institucional ${listaDominios}.` : 'Como aliado externo puedes usar tu correo personal o el de tu organización.'} />
        <CampoContrasena
          etiqueta="Contraseña (mínimo 8 caracteres)"
          valor={form.password}
          alCambiar={(v) => set('password', v)}
          autoComplete="new-password"
          minLength={8}
        />
        <div>
          <CampoContrasena
            id="confirmacion"
            etiqueta="Repite la contraseña"
            valor={confirmacion}
            alCambiar={(v) => {
              setConfirmacion(v)
              if (error === 'Las contraseñas no coinciden.') setError(null)
            }}
            autoComplete="new-password"
            minLength={8}
          />
          {confirmacion && confirmacion !== form.password && (
            <p className="mt-1.5 text-sm text-rose-600 dark:text-rose-400">Las contraseñas no coinciden.</p>
          )}
        </div>
        <div>
          <label className="label" htmlFor="programa">{institucional ? 'Programa o dependencia' : 'Organización'}</label>
          {institucional ? (
            <select id="programa" required className="input" value={form.programa ?? ''} onChange={(e) => set('programa', e.target.value)}>
              <option value="" disabled>Selecciona tu programa</option>
              {PROGRAMAS.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          ) : (
            <input id="programa" className="input" value={form.programa ?? ''} onChange={(e) => set('programa', e.target.value)} />
          )}
        </div>
        {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}
        <button type="submit" className="btn-primary w-full justify-center" disabled={enviando}>
          {enviando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <UserPlus size={15} aria-hidden />}
          Crear cuenta
        </button>
      </section>
    </form>
  )
}
