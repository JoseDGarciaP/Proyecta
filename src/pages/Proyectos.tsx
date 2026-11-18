import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Download, LayoutGrid, Loader2, Table2 } from 'lucide-react'
import { useDatos } from '@/hooks/useDatos'
import { exportarProyectosCsv } from '@/lib/api'
import { ESTADOS, ESTADO_LABEL, type Estado } from '@/lib/types'
import { useAreas, useOds } from '@/lib/parametros'
import { PROGRAMAS } from '@/lib/programas'
import { ProyectoCard } from '@/components/ProyectoCard'
import { EmptyState, EstadoBadge, Progress, Skeleton } from '@/components/ui'
import { formatCompactCOP, formatDate } from '@/lib/format'

/** Resultados por página en el explorador (HU-03). */
const POR_PAGINA = 12

export function Proyectos() {
  const areas = useAreas()
  const catalogoOds = useOds()
  const { proyectos, cargando } = useDatos()
  const [params, setParams] = useSearchParams()
  const [vista, setVista] = useState<'tarjetas' | 'tabla'>('tarjetas')
  const [exportando, setExportando] = useState(false)

  const q = params.get('q') ?? ''
  const estado = params.get('estado') ?? ''
  const area = params.get('area') ?? ''
  const ods = params.get('ods') ?? ''
  const programa = params.get('programa') ?? ''

  /** Cambia un filtro y vuelve a la primera página. */
  const actualizar = (clave: string, valor: string) => {
    const siguiente = new URLSearchParams(params)
    if (valor) siguiente.set(clave, valor)
    else siguiente.delete(clave)
    if (clave !== 'pagina') siguiente.delete('pagina')
    setParams(siguiente, { replace: true })
  }

  /** Programas de la lista de registro más los que ya aparecen en los proyectos. */
  const programas = useMemo(
    () => [...new Set([...PROGRAMAS, ...proyectos.map((p) => p.programa).filter((x): x is string => Boolean(x))])].sort(),
    [proyectos],
  )

  const filtrados = useMemo(() => {
    const texto = q.trim().toLowerCase()
    return proyectos.filter((p) => {
      const coincideTexto =
        !texto ||
        [p.titulo, p.resumen, p.necesidades ?? '', p.lider, ...p.etiquetas].some((v) => v.toLowerCase().includes(texto))
      return (
        coincideTexto &&
        (!estado || p.estado === estado) &&
        (!area || p.area === area) &&
        (!ods || (p.ods ?? []).includes(Number(ods))) &&
        (!programa || p.programa === programa)
      )
    })
  }, [proyectos, q, estado, area, ods, programa])

  const totalPaginas = Math.max(1, Math.ceil(filtrados.length / POR_PAGINA))
  const pagina = Math.min(Math.max(1, Number(params.get('pagina')) || 1), totalPaginas)
  const visibles = filtrados.slice((pagina - 1) * POR_PAGINA, pagina * POR_PAGINA)
  const hayFiltros = Boolean(q || estado || area || ods || programa)

  const descargarCsv = async () => {
    setExportando(true)
    try {
      await exportarProyectosCsv({ q: q.trim(), area, estado, ods, programa }, filtrados)
    } finally {
      setExportando(false)
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Proyectos e iniciativas</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {cargando ? 'Cargando…' : `${filtrados.length} de ${proyectos.length} registros`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="btn-ghost text-sm"
            onClick={descargarCsv}
            disabled={cargando || filtrados.length === 0 || exportando}
          >
            {exportando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Download size={15} aria-hidden />}
            Exportar CSV
          </button>
          <div className="flex gap-1 rounded-lg border border-slate-200 p-1 dark:border-slate-800">
            <button
              className={`btn px-2.5 py-1.5 ${vista === 'tarjetas' ? 'bg-slate-100 dark:bg-slate-800' : ''}`}
              onClick={() => setVista('tarjetas')}
              aria-label="Ver como tarjetas"
            >
              <LayoutGrid size={15} />
            </button>
            <button
              className={`btn px-2.5 py-1.5 ${vista === 'tabla' ? 'bg-slate-100 dark:bg-slate-800' : ''}`}
              onClick={() => setVista('tabla')}
              aria-label="Ver como tabla"
            >
              <Table2 size={15} />
            </button>
          </div>
        </div>
      </header>

      <div className="card flex flex-wrap items-end gap-3 p-4">
        <div className="min-w-56 flex-1">
          <label className="label" htmlFor="f-q">Búsqueda</label>
          <input
            id="f-q"
            className="input"
            value={q}
            placeholder="Título, resumen, necesidades, líder o etiqueta"
            onChange={(e) => actualizar('q', e.target.value)}
          />
        </div>
        <div className="w-44">
          <label className="label" htmlFor="f-estado">Estado</label>
          <select id="f-estado" className="input" value={estado} onChange={(e) => actualizar('estado', e.target.value)}>
            <option value="">Todos</option>
            {ESTADOS.map((e) => (
              <option key={e} value={e}>{ESTADO_LABEL[e as Estado]}</option>
            ))}
          </select>
        </div>
        <div className="w-44">
          <label className="label" htmlFor="f-area">Área</label>
          <select id="f-area" className="input" value={area} onChange={(e) => actualizar('area', e.target.value)}>
            <option value="">Todas</option>
            {areas.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
        <div className="w-52">
          <label className="label" htmlFor="f-ods">ODS</label>
          <select id="f-ods" className="input" value={ods} onChange={(e) => actualizar('ods', e.target.value)}>
            <option value="">Todos</option>
            {catalogoOds.map((o) => (
              <option key={o.id} value={o.id}>{o.id}. {o.nombre}</option>
            ))}
          </select>
        </div>
        <div className="w-52">
          <label className="label" htmlFor="f-programa">Programa</label>
          <select id="f-programa" className="input" value={programa} onChange={(e) => actualizar('programa', e.target.value)}>
            <option value="">Todos</option>
            {programas.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        {hayFiltros && (
          <button type="button" className="btn-ghost text-sm" onClick={() => setParams(new URLSearchParams(), { replace: true })}>
            Limpiar filtros
          </button>
        )}
      </div>

      {cargando ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-56" />)}
        </div>
      ) : filtrados.length === 0 ? (
        <EmptyState
          titulo="Sin resultados"
          detalle="Ajusta los filtros o registra un nuevo proyecto para verlo aquí."
          accion={<Link to="/proyectos/nuevo" className="btn-primary mt-2">Registrar proyecto</Link>}
        />
      ) : vista === 'tarjetas' ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {visibles.map((p) => <ProyectoCard key={p.id} proyecto={p} />)}
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-3xl text-left text-sm">
            <thead className="border-b border-slate-200 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Proyecto</th>
                <th className="px-4 py-3 font-medium">Área</th>
                <th className="px-4 py-3 font-medium">ODS</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Avance</th>
                <th className="px-4 py-3 font-medium">Presupuesto</th>
                <th className="px-4 py-3 font-medium">Inicio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {visibles.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <td className="px-4 py-3">
                    <Link to={`/proyectos/${p.id}`} className="font-medium text-slate-800 hover:text-brand-700 dark:text-slate-100 dark:hover:text-brand-400">
                      {p.titulo}
                    </Link>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{p.lider}</p>
                  </td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{p.area}</td>
                  <td className="px-4 py-3 text-slate-600 tabular-nums dark:text-slate-400">
                    {(p.ods ?? []).length ? (p.ods ?? []).join(', ') : '—'}
                  </td>
                  <td className="px-4 py-3"><EstadoBadge estado={p.estado} /></td>
                  <td className="w-40 px-4 py-3">
                    <Progress valor={p.avance} />
                    <span className="text-xs text-slate-500 tabular-nums dark:text-slate-400">{p.avance}%</span>
                  </td>
                  <td className="px-4 py-3 text-slate-600 tabular-nums dark:text-slate-400">{formatCompactCOP(p.presupuesto)}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{formatDate(p.fecha_inicio)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!cargando && totalPaginas > 1 && (
        <nav className="flex items-center justify-between gap-3 text-sm" aria-label="Paginación de proyectos">
          <p className="text-slate-500 dark:text-slate-400">
            Mostrando {(pagina - 1) * POR_PAGINA + 1}–{Math.min(pagina * POR_PAGINA, filtrados.length)} de {filtrados.length}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn-ghost px-2.5 py-1.5"
              disabled={pagina <= 1}
              onClick={() => actualizar('pagina', String(pagina - 1))}
              aria-label="Página anterior"
            >
              <ChevronLeft size={15} aria-hidden />
            </button>
            <span className="tabular-nums text-slate-600 dark:text-slate-300">Página {pagina} de {totalPaginas}</span>
            <button
              type="button"
              className="btn-ghost px-2.5 py-1.5"
              disabled={pagina >= totalPaginas}
              onClick={() => actualizar('pagina', String(pagina + 1))}
              aria-label="Página siguiente"
            >
              <ChevronRight size={15} aria-hidden />
            </button>
          </div>
        </nav>
      )}
    </div>
  )
}
