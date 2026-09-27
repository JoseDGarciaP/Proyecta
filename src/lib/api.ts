import { apiHabilitada, pedir } from './http'
import { actoresMock, oportunidadesMock, proyectosMock } from '@/data/mock'
import type { Actor, Metricas, NuevoProyecto, Oportunidad, Proyecto } from './types'
import { ESTADOS } from './types'
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

export async function listarActores(): Promise<Actor[]> {
  if (apiHabilitada) return pedir<Actor[]>('/actores')
  await espera(150)
  return actoresMock
}

export async function listarOportunidades(): Promise<Oportunidad[]> {
  if (apiHabilitada) return pedir<Oportunidad[]>('/oportunidades')
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

  return { total, enEjecucion, actores: actores.length, presupuesto, avancePromedio, porEstado, porArea, porMes }
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
