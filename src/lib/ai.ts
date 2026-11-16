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
  fortalezas?: string[]
  pasos_sugeridos?: string[]
  simulado: boolean
}

export interface RespuestaPitch {
  pitch: string
  puntos_clave: string[]
  simulado: boolean
}

/**
 * Pide a la API un resumen ejecutivo, diagnóstico de formulación y oportunidades afines (módulo backend/app/modules/ia).
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

/**
 * Redacta un borrador de carta de postulación cruzando el proyecto con una oportunidad de apoyo.
 */
export async function redactarPitch(
  proyectoId: string,
  oportunidad: Pick<Oportunidad, 'id' | 'titulo' | 'entidad'>,
  proyectoTitulo?: string,
): Promise<RespuestaPitch> {
  if (apiHabilitada) {
    try {
      return await pedir<RespuestaPitch>(`/ia/proyectos/${proyectoId}/pitch/${oportunidad.id}`, { method: 'POST' })
    } catch {
      // cae a borrador heurístico local
    }
  }
  const nombre = proyectoTitulo ? `«${proyectoTitulo}»` : 'nuestro proyecto'
  return {
    pitch:
      `Nuestro equipo presenta ${nombre} a la convocatoria «${oportunidad.titulo}» de ${oportunidad.entidad}. ` +
      `La iniciativa aborda una problemática real validada desde la universidad, cuenta con equipo activo y un plan ` +
      `de trabajo estructurado. Este apoyo permitirá escalar el alcance técnico, fortalecer los entregables y ` +
      `transferir los resultados a los beneficiarios.`,
    puntos_clave: [
      `Dirigido a «${oportunidad.titulo}» (${oportunidad.entidad}).`,
      'Estructura recomendada: problema, avance actual y uso del apoyo.',
    ],
    simulado: true,
  }
}

function diagnosticarLocal(proyecto: Proyecto): { fortalezas: string[]; pasos_sugeridos: string[] } {
  const fortalezas: string[] = []
  const pasos_sugeridos: string[] = []

  if (proyecto.ods && proyecto.ods.length > 0) {
    fortalezas.push(`Alineado con ${proyecto.ods.length} ODS (${proyecto.ods.map((n) => `ODS ${n}`).join(', ')}).`)
  } else {
    pasos_sugeridos.push('Asociar al menos un ODS para mejorar el cruce con convocatorias.')
  }

  if ((proyecto.descripcion ?? '').trim().length >= 80) {
    fortalezas.push('Cuenta con una descripción técnica detallada del alcance.')
  } else {
    pasos_sugeridos.push('Ampliar la descripción del proyecto explicando metodología y resultados esperados.')
  }

  if ((proyecto.necesidades ?? '').trim()) {
    fortalezas.push('Define explícitamente qué perfiles o apoyos necesita sumar.')
  } else {
    pasos_sugeridos.push('Detallar en «Lo que necesita» las habilidades o recursos requeridos.')
  }

  if (proyecto.actores.length > 0) {
    fortalezas.push(`Articulado con ${proyecto.actores.length} actor(es) vinculado(s).`)
  } else {
    pasos_sugeridos.push('Vincular al menos un actor aliado para respaldar la iniciativa.')
  }

  return { fortalezas: fortalezas.slice(0, 4), pasos_sugeridos: pasos_sugeridos.slice(0, 4) }
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

  const { fortalezas, pasos_sugeridos } = diagnosticarLocal(proyecto)

  return {
    resumen:
      `${proyecto.titulo} es una iniciativa del área de ${proyecto.area} liderada por ${proyecto.lider}, ` +
      `con un avance del ${proyecto.avance}%. ${proyecto.resumen} ` +
      `Trabaja con ${proyecto.actores.length} actor(es) vinculado(s) y ${proyecto.equipo.length} integrante(s).`,
    recomendaciones,
    fortalezas,
    pasos_sugeridos,
    simulado: true,
  }
}
