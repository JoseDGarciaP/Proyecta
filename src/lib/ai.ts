import { apiHabilitada, pedir } from './http'
import type { Oportunidad, Proyecto } from './types'

export interface Recomendacion {
  oportunidad_id: string
  titulo: string
  puntaje: number
  razon: string
}

export interface RespuestaIA {
  resumen: string
  recomendaciones: Recomendacion[]
  simulado: boolean
}

/**
 * Pide a la API un resumen ejecutivo y oportunidades afines (módulo backend/app/modules/ia).
 * En modo demostración, o si la API no responde, cae a una heurística local.
 */
export async function analizarProyecto(
  proyecto: Proyecto,
  oportunidades: Oportunidad[],
): Promise<RespuestaIA> {
  if (apiHabilitada) {
    try {
      return await pedir<RespuestaIA>(`/ia/proyectos/${proyecto.id}/analisis`, { method: 'POST' })
    } catch {
      // se ignora y se usa el modo local
    }
  }
  return heuristicaLocal(proyecto, oportunidades)
}

function heuristicaLocal(proyecto: Proyecto, oportunidades: Oportunidad[]): RespuestaIA {
  const recomendaciones = oportunidades
    .map((o) => {
      const afinArea = o.areas.includes(proyecto.area) ? 0.6 : 0
      const afinTexto = o.titulo.toLowerCase().split(/\s+/).some((w) =>
        proyecto.etiquetas.some((e) => e.toLowerCase().includes(w)),
      )
        ? 0.25
        : 0
      const vigencia = new Date(o.cierra_en) > new Date() ? 0.15 : 0
      return {
        oportunidad_id: o.id,
        titulo: o.titulo,
        puntaje: Number((afinArea + afinTexto + vigencia).toFixed(2)),
        razon: afinArea
          ? `Cubre el área de ${proyecto.area} y sigue abierta.`
          : 'Coincidencia parcial por temática y vigencia.',
      }
    })
    .filter((r) => r.puntaje > 0)
    .sort((a, b) => b.puntaje - a.puntaje)
    .slice(0, 3)

  return {
    resumen:
      `${proyecto.titulo} es una iniciativa del área de ${proyecto.area} liderada por ${proyecto.lider}, ` +
      `con un avance del ${proyecto.avance}%. ${proyecto.resumen} ` +
      `Trabaja con ${proyecto.actores.length} actor(es) vinculado(s) y ${proyecto.equipo.length} integrante(s).`,
    recomendaciones,
    simulado: true,
  }
}
