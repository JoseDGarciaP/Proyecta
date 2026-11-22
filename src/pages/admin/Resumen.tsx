import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Download, Loader2 } from 'lucide-react'
import { descargarReportePanel, estadisticas, estadisticasDetalle, exportarReporteInstitucional, type ConteoClave } from '@/lib/admin'
import { Skeleton } from '@/components/ui'
import { Aviso, Tarjeta, useCarga } from './comun'

const ESTADO: Record<string, { label: string; color: string }> = {
  pendiente: { label: 'Pendientes', color: 'bg-amber-500' },
  aceptada: { label: 'Aprobadas', color: 'bg-emerald-600' },
  rechazada: { label: 'Rechazadas', color: 'bg-rose-600' },
  cancelada: { label: 'Retiradas', color: 'bg-slate-400' },
  anulada: { label: 'Anuladas', color: 'bg-slate-600' },
}

export function Resumen() {
  const { datos: e, error } = useCarga(estadisticas)
  const [exportando, setExportando] = useState(false)

  const descargarReporte = async () => {
    setExportando(true)
    try {
      await exportarReporteInstitucional()
    } finally {
      setExportando(false)
    }
  }

  if (error) return <Aviso>{error}</Aviso>
  if (!e) return <Skeleton className="h-96" />

  const totalSolicitudes = e.solicitudes_por_estado.reduce((s, c) => s + c.total, 0)
  const maxMotivo = Math.max(1, ...e.motivos.map((m) => m.total))
  const maxAporte = Math.max(1, ...e.aportes.map((a) => a.total))

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Indicadores consolidados de usuarios, proyectos, alianzas y notificaciones.
        </p>
        <button
          type="button"
          className="btn-ghost text-xs"
          onClick={descargarReporte}
          disabled={exportando}
        >
          {exportando ? <Loader2 size={14} className="animate-spin" aria-hidden /> : <Download size={14} aria-hidden />}
          Exportar reporte institucional (CSV)
        </button>
      </div>

      <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Cifra titulo="Usuarios activos" valor={e.usuarios_activos} detalle={`${e.usuarios_total} cuentas en total`} enlace="/admin/usuarios" />
        <Cifra titulo="Sin verificar" valor={e.usuarios_sin_verificar} detalle={`${e.usuarios_inactivos} desactivadas`} enlace="/admin/usuarios" />
        <Cifra titulo="Proyectos" valor={e.proyectos} detalle={`${e.actores} actores · ${e.oportunidades_abiertas} oportunidades abiertas`} enlace="/admin/moderacion" />
        <Cifra titulo="Correos enviados" valor={e.correos_30_dias} detalle="últimos 30 días" enlace="/admin/ajustes" />
      </dl>

      <div className="grid gap-6 lg:grid-cols-2">
        <Tarjeta titulo="Solicitudes de colaboración" descripcion={
          e.tasa_aprobacion === null ? 'Aún no hay decisiones.' : `Tasa de aprobación: ${Math.round(e.tasa_aprobacion * 100)}% de las decididas.`
        }>
          {totalSolicitudes === 0 ? (
            <p className="text-sm text-slate-500">Todavía no hay solicitudes.</p>
          ) : (
            <>
              <div className="flex h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" aria-hidden>
                {e.solicitudes_por_estado.filter((c) => c.total).map((c) => (
                  <div key={c.clave} className={ESTADO[c.clave].color} style={{ width: `${(c.total / totalSolicitudes) * 100}%` }} />
                ))}
              </div>
              <ul className="mt-3 grid grid-cols-2 gap-2 text-sm">
                {e.solicitudes_por_estado.map((c) => (
                  <li key={c.clave} className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${ESTADO[c.clave].color}`} aria-hidden />
                    <span className="text-slate-600 dark:text-slate-300">{ESTADO[c.clave].label}</span>
                    <span className="ml-auto font-semibold tabular-nums text-slate-900 dark:text-white">{c.total}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </Tarjeta>

        <Tarjeta titulo="Usuarios por rol">
          <ul className="space-y-2 text-sm">
            {[...e.usuarios_por_rol].sort((a, b) => b.total - a.total).map((c) => (
              <li key={c.clave} className="flex items-center gap-3">
                <span className="w-32 text-slate-600 dark:text-slate-300">{c.clave}</span>
                <span className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <span className="block h-full rounded-full bg-accent-500" style={{ width: `${(c.total / Math.max(1, e.usuarios_total)) * 100}%` }} />
                </span>
                <span className="w-8 text-right font-semibold tabular-nums">{c.total}</span>
              </li>
            ))}
          </ul>
        </Tarjeta>

        <Tarjeta titulo="Motivos más usados" descripcion="Al aprobar o rechazar colaboraciones.">
          {e.motivos.length === 0 ? <p className="text-sm text-slate-500">Aún no hay decisiones con motivo.</p> : (
            <ul className="space-y-2.5 text-sm">
              {e.motivos.map((m) => (
                <li key={`${m.tipo}-${m.motivo}`}>
                  <div className="flex justify-between gap-3">
                    <span className="text-slate-700 dark:text-slate-200">{m.motivo}</span>
                    <span className="font-semibold tabular-nums">{m.total}</span>
                  </div>
                  <span className="mt-1 block h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <span className={`block h-full rounded-full ${m.tipo === 'aprobacion' ? 'bg-emerald-600' : 'bg-rose-600'}`} style={{ width: `${(m.total / maxMotivo) * 100}%` }} />
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>

        <Tarjeta titulo="Aportes más propuestos" descripcion="Rol elegido en las solicitudes e invitaciones.">
          {e.aportes.length === 0 ? <p className="text-sm text-slate-500">Sin datos todavía.</p> : (
            <ul className="space-y-2.5 text-sm">
              {e.aportes.map((a) => (
                <li key={a.clave}>
                  <div className="flex justify-between gap-3">
                    <span className="text-slate-700 dark:text-slate-200">{a.clave}</span>
                    <span className="font-semibold tabular-nums">{a.total}</span>
                  </div>
                  <span className="mt-1 block h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <span className="block h-full rounded-full bg-brand-600 dark:bg-brand-300" style={{ width: `${(a.total / maxAporte) * 100}%` }} />
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Tarjeta>
      </div>

      <DetallePeriodo />
    </div>
  )
}

const pct = (x: number | null) => (x === null ? 'Sin datos' : `${Math.round(x * 100)} %`)

function Barras({ datos }: { datos: ConteoClave[] }) {
  const max = Math.max(1, ...datos.map((d) => d.total))
  if (datos.length === 0) return <p className="text-sm text-slate-500">Sin datos en el periodo.</p>
  return (
    <ul className="space-y-2 text-sm">
      {datos.map((c) => (
        <li key={c.clave} className="flex items-center gap-3">
          <span className="w-40 truncate text-slate-600 dark:text-slate-300" title={c.clave}>{c.clave}</span>
          <span className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <span className="block h-full rounded-full bg-brand-600 dark:bg-brand-300" style={{ width: `${(c.total / max) * 100}%` }} />
          </span>
          <span className="w-8 text-right font-semibold tabular-nums">{c.total}</span>
        </li>
      ))}
    </ul>
  )
}

/** Estadísticas por periodo: programa, mes, éxito de postulaciones y recomendaciones (Ep4-Hu28 a Hu30). */
function DetallePeriodo() {
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const { datos: d, error } = useCarga(() => estadisticasDetalle(desde, hasta), [desde, hasta])
  const [bajando, setBajando] = useState(false)
  const bajar = async () => {
    setBajando(true)
    try {
      await descargarReportePanel(desde, hasta)
    } finally {
      setBajando(false)
    }
  }
  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <h2 className="mr-auto font-semibold text-slate-900 dark:text-white">Por periodo</h2>
        <label className="text-xs text-slate-500">Desde <input type="date" className="input mt-1" value={desde} onChange={(e) => setDesde(e.target.value)} /></label>
        <label className="text-xs text-slate-500">Hasta <input type="date" className="input mt-1" value={hasta} onChange={(e) => setHasta(e.target.value)} /></label>
        <button type="button" className="btn-ghost text-xs" onClick={bajar} disabled={bajando}>
          {bajando ? <Loader2 size={14} className="animate-spin" aria-hidden /> : <Download size={14} aria-hidden />} Exportar panel (Excel)
        </button>
      </div>
      <Aviso>{error}</Aviso>
      {!d ? <Skeleton className="h-64" /> : (
        <>
          <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="card p-4"><dt className="text-xs text-slate-500">Proyectos registrados</dt><dd className="mt-1 text-2xl font-semibold tabular-nums">{d.proyectos}</dd></div>
            <div className="card p-4"><dt className="text-xs text-slate-500">Postulaciones</dt><dd className="mt-1 text-2xl font-semibold tabular-nums">{d.postulaciones}</dd>
              <dd className="text-xs text-slate-500">Éxito: {pct(d.tasa_exito_postulaciones)}</dd></div>
            <div className="card p-4"><dt className="text-xs text-slate-500">Recomendaciones</dt><dd className="mt-1 text-2xl font-semibold tabular-nums">{d.recomendaciones_generadas}</dd>
              <dd className="text-xs text-slate-500">{d.recomendaciones_aceptadas} aceptadas · {d.recomendaciones_anuladas} descartadas</dd></div>
            <div className="card p-4"><dt className="text-xs text-slate-500">Aceptadas frente a generadas</dt><dd className="mt-1 text-2xl font-semibold tabular-nums">{pct(d.tasa_aceptacion_recomendaciones)}</dd></div>
          </dl>
          <div className="grid gap-6 lg:grid-cols-2">
            <Tarjeta titulo="Proyectos por programa"><Barras datos={d.por_programa} /></Tarjeta>
            <Tarjeta titulo="Proyectos por área"><Barras datos={d.por_area} /></Tarjeta>
          </div>
          <Tarjeta titulo="Evolución mensual" descripcion="Proyectos, alianzas y postulaciones creadas cada mes.">
            {d.por_mes.length === 0 ? <p className="text-sm text-slate-500">Sin datos en el periodo.</p> : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[520px] text-sm">
                  <thead className="text-left text-xs text-slate-500">
                    <tr><th className="py-2">Mes</th><th>Proyectos</th><th>Alianzas</th><th>Aceptadas</th><th>Postulaciones</th><th>Seleccionadas</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 tabular-nums dark:divide-slate-800">
                    {d.por_mes.map((m) => (
                      <tr key={m.mes}><td className="py-1.5">{m.mes}</td><td>{m.proyectos}</td><td>{m.alianzas}</td><td>{m.alianzas_aceptadas}</td><td>{m.postulaciones}</td><td>{m.postulaciones_aceptadas}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Tarjeta>
        </>
      )}
    </section>
  )
}

function Cifra({ titulo, valor, detalle, enlace }: { titulo: string; valor: number; detalle: string; enlace: string }) {
  return (
    <Link to={enlace} className="card block p-4 transition hover:border-brand-300 dark:hover:border-brand-500/40">
      <dt className="text-xs text-slate-500 dark:text-slate-400">{titulo}</dt>
      <dd className="mt-1 text-2xl font-semibold tabular-nums text-slate-900 dark:text-white">{valor}</dd>
      <dd className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{detalle}</dd>
    </Link>
  )
}
