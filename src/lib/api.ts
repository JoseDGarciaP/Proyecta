import { supabase, supabaseHabilitado } from './supabase'
import { actoresMock, oportunidadesMock, proyectosMock } from '@/data/mock'
import type { Actor, Metricas, Oportunidad, Proyecto } from './types'
import { ESTADOS } from './types'
import { slug } from './format'

/**
 * Capa de datos única para toda la app.
 * Si hay credenciales de Supabase consulta las tablas; si no, trabaja en memoria
 * sobre los datos de ejemplo para que la maqueta sea navegable sin backend.
 */

let memoria: Proyecto[] = [...proyectosMock]

export async function listarProyectos(): Promise<Proyecto[]> {
  if (supabaseHabilitado && supabase) {
    const { data, error } = await supabase
      .from('proyectos')
      .select('*')
      .order('creado_en', { ascending: false })
    if (error) throw new Error(error.message)
    return (data ?? []) as Proyecto[]
  }
  await espera(220)
  return [...memoria]
}

export async function obtenerProyecto(id: string): Promise<Proyecto | null> {
  if (supabaseHabilitado && supabase) {
    const { data, error } = await supabase.from('proyectos').select('*').eq('id', id).maybeSingle()
    if (error) throw new Error(error.message)
    return (data as Proyecto) ?? null
  }
  await espera(120)
  return memoria.find((p) => p.id === id) ?? null
}

export async function crearProyecto(entrada: Omit<Proyecto, 'id' | 'creado_en'>): Promise<Proyecto> {
  const nuevo: Proyecto = {
    ...entrada,
    id: slug(),
    creado_en: new Date().toISOString().slice(0, 10),
  }
  if (supabaseHabilitado && supabase) {
    const { data, error } = await supabase.from('proyectos').insert(nuevo).select().single()
    if (error) throw new Error(error.message)
    return data as Proyecto
  }
  await espera(260)
  memoria = [nuevo, ...memoria]
  return nuevo
}

export async function listarActores(): Promise<Actor[]> {
  if (supabaseHabilitado && supabase) {
    const { data, error } = await supabase.from('actores').select('*').order('nombre')
    if (error) throw new Error(error.message)
    return (data ?? []) as Actor[]
  }
  await espera(150)
  return actoresMock
}

export async function listarOportunidades(): Promise<Oportunidad[]> {
  if (supabaseHabilitado && supabase) {
    const { data, error } = await supabase.from('oportunidades').select('*').order('cierra_en')
    if (error) throw new Error(error.message)
    return (data ?? []) as Oportunidad[]
  }
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
