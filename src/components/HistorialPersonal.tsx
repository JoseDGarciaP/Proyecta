import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Printer } from 'lucide-react'
import { exportarMiHistorial, miHistorial, type EventoHistorial } from '@/lib/seguimiento'

const TIPOS: [EventoHistorial['tipo'] | '', string][] = [
  ['', 'Todo'], ['proyecto', 'Proyectos'], ['alianza', 'Alianzas'], ['postulacion', 'Postulaciones'], ['aporte', 'Aportes'], ['logro', 'Logros'],
]

/** Mi historial en Proyecta, filtrable por tipo y año, para descargar en Excel o imprimir en PDF (Ep4-Hu10, Ep4-Hu16). */
export function HistorialPersonal() {
  const [tipo, setTipo] = useState<EventoHistorial['tipo'] | ''>('')
  const [anio, setAnio] = useState('')
  const [eventos, setEventos] = useState<EventoHistorial[] | null>(null)
  const anioActual = new Date().getFullYear()

  useEffect(() => {
    miHistorial(tipo, anio).then(setEventos).catch(() => setEventos([]))
  }, [tipo, anio])

  return (
    <section className="card p-5" id="historial">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="mr-auto font-semibold text-slate-900 dark:text-white">Mi historial</h2>
        <select className="input w-auto text-sm" aria-label="Tipo" value={tipo} onChange={(e) => setTipo(e.target.value as typeof tipo)}>
          {TIPOS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select className="input w-auto text-sm" aria-label="Año" value={anio} onChange={(e) => setAnio(e.target.value)}>
          <option value="">Todos los años</option>
          {[0, 1, 2, 3].map((i) => <option key={i} value={anioActual - i}>{anioActual - i}</option>)}
        </select>
        <button type="button" className="btn-ghost no-print text-xs" onClick={() => exportarMiHistorial(tipo, anio).catch(() => {})}>
          <Download size={13} aria-hidden /> Excel
        </button>
        <button type="button" className="btn-ghost no-print text-xs" onClick={() => window.print()}>
          <Printer size={13} aria-hidden /> PDF
        </button>
      </div>
      {eventos === null ? <p className="mt-3 text-sm text-slate-500">Cargando…</p> : eventos.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No hay actividad con ese filtro.</p>
      ) : (
        <ol className="mt-3 space-y-2 text-sm">
          {eventos.map((e, i) => (
            <li key={i} className="flex gap-3">
              <time className="w-24 shrink-0 text-xs text-slate-400 tabular-nums">{e.fecha.slice(0, 10)}</time>
              <div className="min-w-0">
                <Link to={e.enlace} className="font-medium text-slate-800 hover:text-brand-700 dark:text-slate-200">{e.titulo}</Link>
                <p className="text-xs text-slate-500 dark:text-slate-400">{e.detalle} · {e.estado}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
