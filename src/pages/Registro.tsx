import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Loader2, UserPlus } from 'lucide-react'
import { useSesion, type DatosRegistro } from '@/lib/sesion'
import type { Rol } from '@/lib/types'
import { BotonGoogle } from '@/components/BotonGoogle'
import { AvisoVerificacion } from '@/components/AvisoVerificacion'
import { CampoCorreo } from '@/components/CampoCorreo'
import { revisarCorreo } from '@/lib/correo'

const ROLES_REGISTRO: { valor: Rol; etiqueta: string }[] = [
  { valor: 'estudiante', etiqueta: 'Estudiante' },
  { valor: 'docente', etiqueta: 'Docente' },
  { valor: 'administrativo', etiqueta: 'Administrativo' },
  { valor: 'aliado', etiqueta: 'Aliado externo' },
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
  const institucional = form.rol !== 'aliado'

  const set = <K extends keyof DatosRegistro>(clave: K, valor: DatosRegistro[K]) => setForm((f) => ({ ...f, [clave]: valor }))

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setIntento(true)
    const revision = revisarCorreo(form.email, { institucional })
    if (revision.error) return
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
          Estudiantes, docentes y administrativos se registran con su correo @ufpso.edu.co. Te enviaremos un enlace para confirmar que el correo es tuyo.
        </p>
      </header>
      <section className="card space-y-4 p-6">
        <BotonGoogle alIngresar={conGoogle} />
        <div>
          <label className="label" htmlFor="nombre">Nombre completo</label>
          <input id="nombre" required minLength={3} className="input" value={form.nombre} onChange={(e) => set('nombre', e.target.value)} />
        </div>
        <CampoCorreo valor={form.email} alCambiar={(v) => set('email', v)} institucional={institucional} forzarRevision={intento} />
        <div>
          <label className="label" htmlFor="password">Contraseña (mínimo 8 caracteres)</label>
          <input id="password" type="password" required minLength={8} autoComplete="new-password" className="input" value={form.password} onChange={(e) => set('password', e.target.value)} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="rol">Soy</label>
            <select id="rol" className="input" value={form.rol} onChange={(e) => set('rol', e.target.value as Rol)}>
              {ROLES_REGISTRO.map((r) => <option key={r.valor} value={r.valor}>{r.etiqueta}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="programa">Programa o dependencia</label>
            <input id="programa" className="input" value={form.programa ?? ''} onChange={(e) => set('programa', e.target.value)} />
          </div>
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
