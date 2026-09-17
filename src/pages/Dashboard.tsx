import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Banknote, Building2, Gauge, Rocket } from 'lucide-react'
import { useDatos } from '@/hooks/useDatos'
import { useOscuro } from '@/hooks/useOscuro'
import { calcularMetricas } from '@/lib/api'
import { formatCompactCOP, diasRestantes } from '@/lib/format'
import { StatCard } from '@/components/StatCard'
import { AreasChart, EstadosChart, TendenciaChart } from '@/components/Charts'
import { ProyectoCard } from '@/components/ProyectoCard'
import { SectionTitle, Skeleton } from '@/components/ui'

export function Dashboard() {
  const { proyectos, actores, oportunidades, cargando, error } = useDatos()
  const oscuro = useOscuro()
  const m = useMemo(() => calcularMetricas(proyectos, actores), [proyectos, actores])

  const recientes = useMemo(
    () => [...proyectos].sort((a, b) => b.creado_en.localeCompare(a.creado_en)).slice(0, 3),
    [proyectos],
  )
  const proximas = useMemo(
    () => [...oportunidades].sort((a, b) => a.cierra_en.localeCompare(b.cierra_en)).slice(0, 4),
    [oportunidades],
  )

  if (error) {
    return <p className="card p-6 text-sm text-rose-600 dark:text-rose-400">{error}</p>
  }

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Panel general</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Estado consolidado de los proyectos registrados y su articulación con actores y oportunidades.
        </p>
      </header>

      {cargando ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard etiqueta="Proyectos registrados" valor={String(m.total)} detalle="en la plataforma" icono={Rocket} />
          <StatCard etiqueta="En ejecución" valor={String(m.enEjecucion)} detalle="con actividades en curso" icono={Gauge} tono="fucsia" />
          <StatCard etiqueta="Actores vinculados" valor={String(m.actores)} detalle="aliados registrados" icono={Building2} />
          <StatCard
            etiqueta="Presupuesto agregado"
            valor={formatCompactCOP(m.presupuesto)}
            detalle={`avance promedio ${m.avancePromedio}%`}
            icono={Banknote}
            tono="fucsia"
          />
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="card p-5 lg:col-span-2">
          <SectionTitle extra={<span className="text-xs text-slate-400">últimos 6 meses</span>}>
            Proyectos nuevos y finalizados
          </SectionTitle>
          {cargando ? <Skeleton className="h-[260px]" /> : <TendenciaChart datos={m.porMes} oscuro={oscuro} />}
        </section>

        <section className="card p-5">
          <SectionTitle>Distribución por estado</SectionTitle>
          {cargando ? <Skeleton className="h-[260px]" /> : <EstadosChart datos={m.porEstado} oscuro={oscuro} />}
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="card p-5 lg:col-span-2">
          <SectionTitle>Proyectos por área de conocimiento</SectionTitle>
          {cargando ? <Skeleton className="h-[260px]" /> : <AreasChart datos={m.porArea} oscuro={oscuro} />}
        </section>

        <section className="card p-5">
          <SectionTitle extra={<Link to="/oportunidades" className="text-xs text-brand-700 dark:text-brand-400">Ver todas</Link>}>
            Cierres próximos
          </SectionTitle>
          <ul className="space-y-3">
            {proximas.map((o) => {
              const dias = diasRestantes(o.cierra_en)
              return (
                <li key={o.id} className="flex items-start justify-between gap-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-800 dark:text-slate-200">{o.titulo}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{o.entidad}</p>
                  </div>
                  <span
                    className={`shrink-0 text-xs tabular-nums ${
                      dias <= 30 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500 dark:text-slate-400'
                    }`}
                  >
                    {dias > 0 ? `${dias} días` : 'cerrada'}
                  </span>
                </li>
              )
            })}
          </ul>
        </section>
      </div>

      <section>
        <SectionTitle extra={<Link to="/proyectos" className="text-xs text-brand-700 dark:text-brand-400">Ver todos</Link>}>
          Registros recientes
        </SectionTitle>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {cargando
            ? Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-56" />)
            : recientes.map((p) => <ProyectoCard key={p.id} proyecto={p} />)}
        </div>
      </section>
    </div>
  )
}
