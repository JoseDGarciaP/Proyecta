import { apiHabilitada, descargarArchivo, ErrorApi, pedir } from './http'
import { actoresMock, oportunidadesMock, proyectosMock } from '@/data/mock'
import type { Actor, Metricas, NuevoProyecto, Oportunidad, Proyecto } from './types'
import { ESTADOS, ODS } from './types'
import { slug } from './format'

/**
 * Capa de datos única para toda la app.
 * Con VITE_API_URL consulta la API (backend FastAPI); si no, trabaja en memoria
 * sobre los datos de ejemplo para que la maqueta sea navegable sin backend.
 */

let memoria: Proyecto[] = [...proyectosMock]

export async function listarProyectos(): Promise<Proyecto[]> {
  if (apiHabilitada) return pedir<Proyecto[]>('/proyectos')
  await espera(220)
  return [...memoria]
}

export async function obtenerProyecto(id: string): Promise<Proyecto | null> {
  if (apiHabilitada) {
    try {
      return await pedir<Proyecto>(`/proyectos/${id}`)
    } catch {
      return null
    }
  }
  await espera(120)
  return memoria.find((p) => p.id === id) ?? null
}

export async function crearProyecto(entrada: NuevoProyecto): Promise<Proyecto> {
  if (apiHabilitada) return pedir<Proyecto>('/proyectos', { method: 'POST', json: entrada })
  const nuevo: Proyecto = {
    ...entrada,
    lider: entrada.lider || 'Usuario de demostración',
    id: slug(),
    creado_en: new Date().toISOString().slice(0, 10),
  }
  await espera(260)
  memoria = [nuevo, ...memoria]
  return nuevo
}

/** Cambia los datos de un proyecto. La API solo lo permite a quien lo registró (o a un admin). */
export async function actualizarProyecto(id: string, cambios: Partial<NuevoProyecto>): Promise<Proyecto> {
  if (apiHabilitada) return pedir<Proyecto>(`/proyectos/${id}`, { method: 'PATCH', json: cambios })
  await espera(200)
  const actual = memoria.find((p) => p.id === id)
  if (!actual) throw new Error('Proyecto no encontrado')
  const nuevo: Proyecto = { ...actual, ...cambios, lider: cambios.lider || actual.lider }
  memoria = memoria.map((p) => (p.id === id ? nuevo : p))
  return nuevo
}

export interface FiltrosExportarProyectos {
  q?: string
  area?: string
  estado?: string
}

function escaparCsv(valor: string | number): string {
  const texto = String(valor ?? '')
  return /[",\n\r]/.test(texto) ? `"${texto.replace(/"/g, '""')}"` : texto
}

/** Descarga los proyectos filtrados en CSV (desde FastAPI o generado localmente en modo demostración). */
export async function exportarProyectosCsv(
  filtros: FiltrosExportarProyectos,
  proyectosVisibles: Proyecto[],
): Promise<void> {
  if (apiHabilitada) {
    const params = new URLSearchParams(
      Object.entries(filtros).filter(([, v]) => Boolean(v)) as [string, string][],
    )
    const qs = params.toString()
    await descargarArchivo(`/proyectos/exportar.csv${qs ? `?${qs}` : ''}`, 'proyectos-proyecta.csv')
    return
  }

  const encabezados = [
    'ID', 'Título', 'Área', 'Estado', 'Avance (%)', 'Presupuesto (COP)',
    'Líder', 'Integrantes equipo', 'ODS', 'Etiquetas', 'Fecha inicio', 'Fecha cierre', 'Registrado en',
  ]
  const filas = proyectosVisibles.map((p) => [
    p.id,
    p.titulo,
    p.area,
    p.estado,
    p.avance,
    p.presupuesto,
    p.lider,
    p.equipo.join(', '),
    (p.ods ?? []).map((n) => `ODS ${n}`).join(', '),
    p.etiquetas.join(', '),
    p.fecha_inicio,
    p.fecha_fin ?? '',
    p.creado_en,
  ])
  const contenido =
    '\ufeff' +
    [encabezados, ...filas].map((fila) => fila.map(escaparCsv).join(',')).join('\r\n')
  const blob = new Blob([contenido], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = 'proyectos-proyecta.csv'
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

/** Si el rol no tiene permiso de ver algo (403), se muestra vacío en lugar de romper la página. */
const sinPermisoVacio = <T,>(p: Promise<T[]>): Promise<T[]> =>
  p.catch((e) => {
    if (e instanceof ErrorApi && e.status === 403) return []
    throw e
  })

export async function listarActores(): Promise<Actor[]> {
  if (apiHabilitada) return sinPermisoVacio(pedir<Actor[]>('/actores'))
  await espera(150)
  return actoresMock
}

export async function listarOportunidades(): Promise<Oportunidad[]> {
  if (apiHabilitada) return sinPermisoVacio(pedir<Oportunidad[]>('/oportunidades'))
  await espera(150)
  return oportunidadesMock
}

export function calcularMetricas(proyectos: Proyecto[], actores: Actor[]): Metricas {
  const total = proyectos.length
  const enEjecucion = proyectos.filter((p) => p.estado === 'ejecucion').length
  const presupuesto = proyectos.reduce((acc, p) => acc + p.presupuesto, 0)
  const avancePromedio = total ? Math.round(proyectos.reduce((a, p) => a + p.avance, 0) / total) : 0

  const porEstado = ESTADOS.map((estado) => ({
    estado,
    total: proyectos.filter((p) => p.estado === estado).length,
  }))

  const areas = new Map<string, number>()
  for (const p of proyectos) areas.set(p.area, (areas.get(p.area) ?? 0) + 1)
  const porArea = [...areas.entries()]
    .map(([area, totalArea]) => ({ area, total: totalArea }))
    .sort((a, b) => b.total - a.total)

  const porMes = ultimosMeses(6).map(({ clave, etiqueta }) => ({
    mes: etiqueta,
    nuevos: proyectos.filter((p) => p.creado_en.slice(0, 7) === clave).length,
    finalizados: proyectos.filter((p) => p.estado === 'finalizado' && p.fecha_fin?.slice(0, 7) === clave).length,
  }))

  const conteoOds = new Map<number, number>()
  for (const p of proyectos) {
    for (const n of p.ods ?? []) {
      conteoOds.set(n, (conteoOds.get(n) ?? 0) + 1)
    }
  }
  const porOds = ODS.map((o) => ({
    id: o.id,
    ods: `ODS ${o.id}`,
    nombre: `ODS ${o.id}: ${o.nombre}`,
    total: conteoOds.get(o.id) ?? 0,
  }))
    .filter((o) => o.total > 0)
    .sort((a, b) => b.total - a.total || a.id - b.id)

  return { total, enEjecucion, actores: actores.length, presupuesto, avancePromedio, porEstado, porArea, porMes, porOds }
}

function ultimosMeses(n: number) {
  const salida: { clave: string; etiqueta: string }[] = []
  const hoy = new Date()
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1)
    salida.push({
      clave: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`,
      etiqueta: d.toLocaleDateString('es-CO', { month: 'short' }).replace('.', ''),
    })
  }
  return salida
}

const espera = (ms: number) => new Promise((r) => setTimeout(r, ms))
