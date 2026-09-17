import { Link } from 'react-router-dom'

export function NoEncontrado() {
  return (
    <div className="mx-auto max-w-md py-20 text-center">
      <p className="text-5xl font-semibold text-slate-300 dark:text-slate-700">404</p>
      <h1 className="mt-3 text-xl font-semibold text-slate-900 dark:text-white">Página no encontrada</h1>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
        La ruta solicitada no existe dentro de la plataforma.
      </p>
      <Link to="/" className="btn-primary mt-6">Ir al panel</Link>
    </div>
  )
}
