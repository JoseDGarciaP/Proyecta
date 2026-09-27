import { pedir } from './http'
import type {
  Miembro,
  Perfil,
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

export const solicitarUnion = (proyectoId: string, mensaje: string) =>
  pedir<Solicitud>(`/proyectos/${proyectoId}/solicitudes`, { method: 'POST', json: { mensaje } })

export const invitar = (proyectoId: string, usuarioId: string, mensaje = '') =>
  pedir<Solicitud>(`/proyectos/${proyectoId}/invitaciones`, { method: 'POST', json: { usuario_id: usuarioId, mensaje } })

export const misSolicitudes = () => pedir<Solicitud[]>('/alianzas')

export function responderSolicitud(id: string, accion: 'aceptar' | 'rechazar' | 'cancelar', respuesta = '') {
  return pedir<Solicitud>(`/alianzas/${id}/${accion}`, {
    method: 'POST',
    json: accion === 'cancelar' ? undefined : { respuesta },
  })
}

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
