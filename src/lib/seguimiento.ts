import { abrirArchivo, descargarArchivo, pedir } from './http'

/** Observación pública sobre un proyecto (Ep4-Hu19). */
export interface Observacion {
  id: string
  proyecto_id: string
  autor_id: string | null
  autor: string
  texto: string
  oculta: boolean
  motivo_oculta: string
  creado_en: string
  editado_en: string | null
}

export interface Adjunto {
  id: string
  nombre: string
  tipo: string
  tamano: number
  subido_por: string
  creado_en: string
}

export interface CambioProyecto {
  id: string
  autor: string
  cambios: { campo: string; antes: string; despues: string }[]
  creado_en: string
}

export const listarObservaciones = (proyectoId: string) => pedir<Observacion[]>(`/proyectos/${proyectoId}/observaciones`)
export const crearObservacion = (proyectoId: string, texto: string) =>
  pedir<Observacion>(`/proyectos/${proyectoId}/observaciones`, { method: 'POST', json: { texto } })
export const editarObservacion = (id: string, texto: string) =>
  pedir<Observacion>(`/observaciones/${id}`, { method: 'PATCH', json: { texto } })
export const borrarObservacion = (id: string) => pedir<void>(`/observaciones/${id}`, { method: 'DELETE' })
export const ocultarObservacion = (id: string, motivo: string) =>
  pedir<Observacion>(`/admin/observaciones/${id}/ocultar`, { method: 'POST', json: { motivo } })
export const restaurarObservacion = (id: string) => pedir<Observacion>(`/admin/observaciones/${id}/restaurar`, { method: 'POST' })

export const listarAdjuntos = (proyectoId: string) => pedir<Adjunto[]>(`/proyectos/${proyectoId}/adjuntos`)
export function subirAdjunto(proyectoId: string, archivo: File) {
  const datos = new FormData()
  datos.append('archivo', archivo)
  return pedir<Adjunto>(`/proyectos/${proyectoId}/adjuntos`, { method: 'POST', datos })
}
export const abrirAdjunto = (a: Adjunto) => abrirArchivo(`/adjuntos/${a.id}/archivo`)
export const borrarAdjunto = (id: string) => pedir<void>(`/adjuntos/${id}`, { method: 'DELETE' })

export const listarCambios = (proyectoId: string) => pedir<CambioProyecto[]>(`/proyectos/${proyectoId}/cambios`)

/** Elimina el proyecto; si tiene colaboradores la API lo archiva y les avisa (Ep4-Hu20). */
export const eliminarProyecto = (proyectoId: string, motivo: string) =>
  pedir<void>(`/proyectos/${proyectoId}`, { method: 'DELETE', json: { motivo } })

/** Aporte de un miembro que el responsable valida (Ep6-Hu11). */
export interface Aporte {
  id: string
  usuario_id: string | null
  usuario: string
  tipo: string
  descripcion: string
  horas: number | null
  valor: number | null
  fecha: string
  estado: 'pendiente' | 'validado' | 'rechazado'
  comentario: string
}
export interface ResumenAportes {
  aportes: Aporte[]
  horas_validadas: number
  valor_validado: number
}
export type NuevoAporte = Pick<Aporte, 'tipo' | 'descripcion' | 'horas' | 'valor' | 'fecha'>

export const listarAportes = (proyectoId: string) => pedir<ResumenAportes>(`/proyectos/${proyectoId}/aportes`)
export const registrarAporte = (proyectoId: string, datos: NuevoAporte) =>
  pedir<Aporte>(`/proyectos/${proyectoId}/aportes`, { method: 'POST', json: datos })
export const revisarAporte = (id: string, accion: 'validar' | 'rechazar', comentario = '') =>
  pedir<Aporte>(`/aportes/${id}/${accion}`, { method: 'POST', json: { comentario } })
export const borrarAporte = (id: string) => pedir<void>(`/aportes/${id}`, { method: 'DELETE' })

/** Historial personal con filtro por tipo y año (Ep4-Hu10, Ep4-Hu16). */
export interface EventoHistorial {
  tipo: 'proyecto' | 'alianza' | 'postulacion' | 'aporte' | 'logro'
  fecha: string
  titulo: string
  detalle: string
  estado: string
  enlace: string
}
const filtroHistorial = (tipo: string, anio: string) => {
  const p = new URLSearchParams(Object.entries({ tipo, anio }).filter(([, v]) => v))
  return p.size ? `?${p}` : ''
}
export const miHistorial = (tipo = '', anio = '') => pedir<EventoHistorial[]>(`/usuarios/yo/historial${filtroHistorial(tipo, anio)}`)
export const exportarMiHistorial = (tipo = '', anio = '') =>
  descargarArchivo(`/usuarios/yo/historial.xlsx${filtroHistorial(tipo, anio)}`, 'mi-historial-proyecta.xlsx')
