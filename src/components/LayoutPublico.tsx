import { Link, NavLink, Outlet } from 'react-router-dom'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'

/** Marco para visitantes: página de inicio, ingreso, registro y verificación de correo. */
export function LayoutPublico() {
  const { tema, alternar } = useTheme()
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/85 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4">
          <Link to="/bienvenida" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-linear-to-br from-brand-600 to-accent-500 text-sm font-bold text-white">P</span>
            <span className="text-base font-semibold tracking-tight text-slate-900 dark:text-white">Proyecta</span>
          </Link>
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={alternar}
              className="btn-ghost px-2.5"
              aria-label={tema === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'}
            >
              {tema === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <NavLink to="/ingresar" className="btn-ghost">Ingresar</NavLink>
            <NavLink to="/registro" className="btn-primary">Crear cuenta</NavLink>
          </div>
        </div>
      </header>
      <main className="flex-1 px-4 py-8 lg:py-12">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 px-4 py-5 text-center text-xs text-slate-400 dark:border-slate-800">
        Proyecta · Universidad Francisco de Paula Santander Ocaña · Proyecto de Ingeniería de Software
      </footer>
    </div>
  )
}
