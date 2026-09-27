import { Link } from 'react-router-dom'
import type { MetodoSimilitud, Sugerencia } from '@/lib/types'
import type { ReactNode } from 'react'

const RUTA: Record<Sugerencia['tipo'], (id: string) => string | null> = {
  proyecto: (id) => `/proyectos/${id}`,
  oportunidad: () => '/oportunidades',
  usuario: () => null,
}

/** Lista de resultados de similitud con su porcentaje y la razón de la sugerencia. */
export function ListaSugerencias({
  items,
  vacio,
  accion,
}: {
  items: Sugerencia[]
  vacio: string
  accion?: (s: Sugerencia) => ReactNode
}) {
  if (items.length === 0) return <p className="text-sm text-slate-500 dark:text-slate-400">{vacio}</p>
  return (
    <ul className="space-y-2">
      {items.map((s) => {
        const ruta = RUTA[s.tipo](s.id)
        return (
          <li key={s.id} className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800">
            <div className="flex items-baseline justify-between gap-3">
              {ruta ? (
                <Link to={ruta} className="font-medium text-slate-800 hover:text-brand-700 dark:text-slate-100 dark:hover:text-brand-300">
                  {s.titulo}
                </Link>
              ) : (
                <span className="font-medium text-slate-800 dark:text-slate-100">{s.titulo}</span>
              )}
              <span className="shrink-0 text-xs text-slate-500 tabular-nums dark:text-slate-400">
                {Math.round(s.similitud * 100)}%
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">{s.detalle}</p>
            <p className="mt-1 text-slate-600 dark:text-slate-400">{s.razon}</p>
            {accion && <div className="mt-2">{accion(s)}</div>}
          </li>
        )
      })}
    </ul>
  )
}

export function NotaMetodo({ metodo }: { metodo: MetodoSimilitud | undefined }) {
  if (metodo !== 'lexico') return null
  return (
    <p className="mt-3 text-xs text-amber-700 dark:text-amber-400">
      Similitud por palabras en común: el modelo de sentence-transformers no está cargado en el backend. Ejecuta
      <code> python -m scripts.indexar_embeddings</code> para descargarlo.
    </p>
  )
}
