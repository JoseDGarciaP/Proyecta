import { Link, NavLink, Outlet } from 'react-router-dom'
import { useTheme } from '@/hooks/useTheme'
import { SelectorTema } from '@/components/SelectorTema'

/** Marco para visitantes: página de inicio, ingreso, registro y verificación de correo. */
export function LayoutPublico() {
  const { preferencia, setPreferencia } = useTheme()
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/85 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-3 px-4">
          <Link to="/bienvenida" className="flex items-center gap-2">
            <span className="marca h-8 w-8 text-base">P</span>
            <span className="text-lg font-bold text-slate-900 [font-stretch:82%] dark:text-white">Proyecta</span>
          </Link>
          <div className="ml-auto flex items-center gap-2">
            <SelectorTema valor={preferencia} onCambio={setPreferencia} />
            <NavLink to="/ingresar" className="btn-ghost">Ingresar</NavLink>
            <NavLink to="/registro" className="btn-primary">Crear cuenta</NavLink>
          </div>
        </div>
      </header>
      <main className="flex-1 px-4 py-8 lg:py-12">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 px-4 py-5 text-center text-xs text-slate-400 dark:border-slate-800">
        Proyecta, plataforma para articular proyectos, actores y oportunidades de apoyo.
      </footer>
    </div>
  )
}
