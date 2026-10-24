import { pedir } from './http'
import type {
  Miembro,
  Perfil,
  Recomendacion,
  RespuestaSugerencias,
  Solicitud,
  SugerenciasParaMi,
  Usuario,
} from './types'

/**
 * Perfil, alianzas y sugerencias por similitud. Solo existen con la API conectada:
 * en modo demostración las páginas muestran un aviso en su lugar.
 */

export const obtenerPerfil = () => pedir<Perfil>('/perfil')

export type CambiosPerfil = Partial<Pick<Usuario, 'nombre' | 'programa' | 'bio' | 'habilidades' | 'intereses'>>
export const actualizarPerfil = (cambios: CambiosPerfil) =>
  pedir<Usuario>('/usuarios/yo', { method: 'PATCH', json: cambios })

export const listarMiembros = (proyectoId: string) => pedir<Miembro[]>(`/proyectos/${proyectoId}/miembros`)

export const solicitarUnion = (proyectoId: string, reco: Recomendacion) =>
  pedir<Solicitud>(`/proyectos/${proyectoId}/solicitudes`, { method: 'POST', json: reco })

export const invitar = (proyectoId: string, usuarioId: string, reco: Recomendacion) =>
  pedir<Solicitud>(`/proyectos/${proyectoId}/invitaciones`, { method: 'POST', json: { ...reco, usuario_id: usuarioId } })

export const misSolicitudes = () => pedir<Solicitud[]>('/alianzas')

/** Aprobar o rechazar exige un motivo del catálogo; el comentario es opcional salvo que el motivo lo pida. */
export const decidirSolicitud = (id: string, accion: 'aceptar' | 'rechazar', motivoId: number, respuesta = '') =>
  pedir<Solicitud>(`/alianzas/${id}/${accion}`, { method: 'POST', json: { motivo_id: motivoId, respuesta } })

export const cancelarSolicitud = (id: string) => pedir<Solicitud>(`/alianzas/${id}/cancelar`, { method: 'POST' })

export const proyectosSimilares = (proyectoId: string) =>
  pedir<RespuestaSugerencias>(`/ia/proyectos/${proyectoId}/similares`)

export const colaboradoresSugeridos = (proyectoId: string) =>
  pedir<RespuestaSugerencias>(`/ia/proyectos/${proyectoId}/colaboradores`)

export const buscarSemantico = (q: string, en: 'oportunidades' | 'proyectos' = 'oportunidades') =>
  pedir<RespuestaSugerencias>(`/ia/buscar?${new URLSearchParams({ q, en })}`)

export const sugerenciasParaMi = () => pedir<SugerenciasParaMi>('/ia/para-mi')

export const listaATexto = (xs: string[]) => xs.join(', ')
export const textoALista = (s: string) =>
  [...new Set(s.split(',').map((x) => x.trim()).filter(Boolean))]
