import type { Oportunidad, Proyecto } from './types'

const base = import.meta.env.VITE_AI_API_URL?.replace(/\/$/, '')

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
 * Pide al servicio de IA (carpeta /ai) un resumen ejecutivo y oportunidades afines.
 * Si el servicio no está configurado o no responde, cae a una heurística local
 * para que la maqueta siga siendo demostrable.
 */
export async function analizarProyecto(
  proyecto: Proyecto,
  oportunidades: Oportunidad[],
): Promise<RespuestaIA> {
  if (base) {
    try {
      const res = await fetch(`${base}/analizar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proyecto, oportunidades }),
      })
      if (res.ok) return (await res.json()) as RespuestaIA
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
