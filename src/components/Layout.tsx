import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Building2,
  LayoutDashboard,
  Lightbulb,
  LogIn,
  LogOut,
  Menu,
  Moon,
  Plus,
  Search,
  Sparkles,
  Sun,
  UserRound,
  X,
} from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'

const NAV = [
  { to: '/', label: 'Panel', icon: LayoutDashboard, end: true },
  { to: '/proyectos', label: 'Proyectos', icon: Lightbulb, end: false },
  { to: '/actores', label: 'Actores', icon: Building2, end: false },
  { to: '/oportunidades', label: 'Oportunidades', icon: Sparkles, end: false },
]

export function Layout() {
  const { tema, alternar } = useTheme()
  const [abierto, setAbierto] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const navegar = useNavigate()
  const { usuario, salir } = useSesion()

  const buscar = (e: React.FormEvent) => {
    e.preventDefault()
    navegar(`/proyectos?q=${encodeURIComponent(busqueda)}`)
    setAbierto(false)
  }

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[248px_1fr]">
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 border-r border-slate-200 bg-white transition-transform lg:static lg:w-auto lg:translate-x-0 dark:border-slate-800 dark:bg-slate-900 ${
          abierto ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center justify-between px-5">
          <span className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-linear-to-br from-brand-600 to-accent-500 text-sm font-bold text-white">P</span>
            <span className="text-base font-semibold tracking-tight text-slate-900 dark:text-white">Proyecta</span>
          </span>
          <button className="lg:hidden" onClick={() => setAbierto(false)} aria-label="Cerrar menú">
            <X size={18} />
          </button>
        </div>

        <nav className="space-y-1 px-3 py-2">
          {[...NAV, ...(usuario ? [{ to: '/perfil', label: 'Mi perfil', icon: UserRound, end: false }] : [])].map(({ to, label, icon: Icono, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={() => setAbierto(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-brand-50 text-brand-800 ring-1 ring-brand-200 dark:bg-brand-500/12 dark:text-brand-200 dark:ring-brand-500/25'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
                }`
              }
            >
              <Icono size={17} aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="mt-4 px-5">
          <div className="rounded-lg border border-dashed border-slate-300 p-3 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-400">
            <p className="font-medium text-slate-700 dark:text-slate-300">
              {apiHabilitada ? 'Conectado a la API' : 'Modo demostración'}
            </p>
            <p className="mt-1 leading-relaxed">
              {apiHabilitada
                ? 'Los datos se leen y escriben a través del backend de Proyecta.'
                : 'Datos de ejemplo en memoria. Define VITE_API_URL para conectar el backend.'}
            </p>
          </div>
        </div>
      </aside>

      {abierto && (
        <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden" onClick={() => setAbierto(false)} aria-hidden />
      )}

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/85 px-4 backdrop-blur lg:px-8 dark:border-slate-800 dark:bg-slate-950/80">
          <button className="lg:hidden" onClick={() => setAbierto(true)} aria-label="Abrir menú">
            <Menu size={20} />
          </button>

          <form onSubmit={buscar} className="relative hidden max-w-sm flex-1 sm:block">
            <Search size={16} className="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" aria-hidden />
            <input
              className="input pl-9"
              placeholder="Buscar proyectos, líderes o etiquetas…"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              aria-label="Buscar proyectos"
            />
          </form>

          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={alternar}
              className="btn-ghost px-2.5"
              aria-label={tema === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'}
            >
              {tema === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            {apiHabilitada &&
              (usuario ? (
                <>
                  <NavLink to="/perfil" className="btn-ghost" title="Mi perfil">
                    <UserRound size={16} aria-hidden />
                    <span className="hidden max-w-40 truncate md:inline">{usuario.nombre}</span>
                  </NavLink>
                  <button onClick={salir} className="btn-ghost px-2.5" title={`Salir (${usuario.email})`}>
                    <LogOut size={16} aria-label="Salir" />
                  </button>
                </>
              ) : (
                <NavLink to="/ingresar" className="btn-ghost">
                  <LogIn size={16} aria-hidden />
                  <span className="hidden sm:inline">Ingresar</span>
                </NavLink>
              ))}
            <NavLink to="/proyectos/nuevo" className="btn-primary">
              <Plus size={16} aria-hidden />
              <span className="hidden sm:inline">Registrar proyecto</span>
            </NavLink>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet context={{ oscuro: tema === 'dark' }} />
        </main>

        <footer className="border-t border-slate-200 px-4 py-5 text-xs text-slate-400 lg:px-8 dark:border-slate-800">
          Proyecta · maqueta funcional para la articulación de proyectos, actores y oportunidades.
        </footer>
      </div>
    </div>
  )
}
