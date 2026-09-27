import { useState } from 'react'
import { Loader2, Sparkles } from 'lucide-react'
import { analizarProyecto, type RespuestaIA } from '@/lib/ai'
import type { Oportunidad, Proyecto } from '@/lib/types'

export function PanelIA({ proyecto, oportunidades }: { proyecto: Proyecto; oportunidades: Oportunidad[] }) {
  const [respuesta, setRespuesta] = useState<RespuestaIA | null>(null)
  const [cargando, setCargando] = useState(false)

  const ejecutar = async () => {
    setCargando(true)
    try {
      setRespuesta(await analizarProyecto(proyecto, oportunidades))
    } finally {
      setCargando(false)
    }
  }

  return (
    <section className="card p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <Sparkles size={16} className="text-brand-600 dark:text-brand-400" aria-hidden />
          Asistente de articulación
        </h2>
        <button className="btn-primary" onClick={ejecutar} disabled={cargando}>
          {cargando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Sparkles size={15} aria-hidden />}
          {cargando ? 'Analizando…' : 'Analizar'}
        </button>
      </div>

      {!respuesta && !cargando && (
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
          Genera un resumen ejecutivo del proyecto y sugiere oportunidades de apoyo afines.
        </p>
      )}

      {respuesta && (
        <div className="mt-4 space-y-4">
          <div>
            <p className="label">Resumen</p>
            <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">{respuesta.resumen}</p>
          </div>

          {respuesta.recomendaciones.length > 0 && (
            <div>
              <p className="label">Oportunidades sugeridas</p>
              <ul className="space-y-2">
                {respuesta.recomendaciones.map((r) => (
                  <li
                    key={r.oportunidad_id}
                    className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800"
                  >
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="font-medium text-slate-800 dark:text-slate-100">{r.titulo}</span>
                      <span className="text-xs text-slate-500 tabular-nums dark:text-slate-400">
                        afinidad {Math.round(r.puntaje * 100)}%
                      </span>
                    </div>
                    <p className="mt-1 text-slate-600 dark:text-slate-400">{r.razon}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {respuesta.simulado && (
            <p className="text-xs text-amber-700 dark:text-amber-400">
              Resumen generado con reglas locales. Define <code>ANTHROPIC_API_KEY</code> en el backend para que lo
              redacte un modelo.
            </p>
          )}
        </div>
      )}
    </section>
  )
}
