import { pedir } from './http'
import type { Mensaje, ResumenChat, Usuario } from './types'

/**
 * Chats de Proyecta: el del equipo de cada proyecto y la conversación de cada solicitud.
 * No hay tiempo real: la página pide lo nuevo cada pocos segundos con `despues_de`
 * (el id del último mensaje que tiene) y `cambios_desde` (para enterarse de ediciones y borrados).
 */

export const INTERVALO_CHAT_MS = 4000

/** Se emite al marcar mensajes como leídos, para que los avisos se actualicen sin esperar. */
export const EVENTO_CHAT_LEIDO = 'proyecta:chat-leido'

export type Cursor = { despues_de?: number; cambios_desde?: string; antes_de?: number }

/** Operaciones de una conversación; el componente de chat no sabe si es de un proyecto o de una solicitud. */
export interface ApiChat {
  listar: (cursor?: Cursor) => Promise<Mensaje[]>
  enviar: (texto: string) => Promise<Mensaje>
  editar: (id: number, texto: string) => Promise<Mensaje>
  eliminar: (id: number) => Promise<void>
  marcarLeidos: (hastaId: number) => Promise<void>
}

function apiChat(ruta: string): ApiChat {
  return {
    listar: (cursor = {}) => {
      const params = new URLSearchParams(
        Object.entries(cursor).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)]),
      )
      return pedir<Mensaje[]>(`${ruta}${params.size ? `?${params}` : ''}`)
    },
    enviar: (texto) => pedir<Mensaje>(ruta, { method: 'POST', json: { texto } }),
    editar: (id, texto) => pedir<Mensaje>(`${ruta}/${id}`, { method: 'PATCH', json: { texto } }),
    eliminar: (id) => pedir<void>(`${ruta}/${id}`, { method: 'DELETE' }),
    marcarLeidos: (hastaId) =>
      pedir<void>(`${ruta}/leidos`, { method: 'POST', json: { hasta_id: hastaId } }).then(() => {
        window.dispatchEvent(new Event(EVENTO_CHAT_LEIDO))
      }),
  }
}

export const chatDeProyecto = (proyectoId: string) => apiChat(`/proyectos/${proyectoId}/mensajes`)

/** Entre quien pide unirse (o fue invitado) y el responsable; solo se escribe mientras está pendiente. */
export const chatDeSolicitud = (solicitudId: string) => apiChat(`/alianzas/${solicitudId}/mensajes`)

export const misChats = () => pedir<ResumenChat[]>('/chats')

export const obtenerUsuario = (id: string) => pedir<Omit<Usuario, 'email'>>(`/usuarios/${id}`)

/** A dónde lleva un aviso de mensajes nuevos. */
export const enlaceDeChat = (c: ResumenChat) =>
  c.tipo === 'proyecto' ? `/proyectos/${c.proyecto_id}#chat` : `/perfil#solicitud-${c.solicitud_id}`
