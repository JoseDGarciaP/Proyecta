import { useEffect, useState } from 'react'
import { EVENTO_CHAT_LEIDO, misChats } from '@/lib/chat'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import type { ResumenChat } from '@/lib/types'

const INTERVALO_MS = 15_000

export interface NoLeidos {
  /** Chats con mensajes sin leer, el más reciente primero. */
  chats: ResumenChat[]
  /** No leídos del chat del equipo, por proyecto. */
  porProyecto: Record<string, number>
  /** No leídos de la conversación de cada solicitud. */
  porSolicitud: Record<string, number>
  total: number
}

/**
 * Mensajes sin leer de mis proyectos y de mis solicitudes, para los avisos del header y del perfil.
 * Se actualiza cada 15 s y en cuanto se leen mensajes en algún chat.
 */
export function useNoLeidos(): NoLeidos {
  const { usuario } = useSesion()
  const [chats, setChats] = useState<ResumenChat[]>([])

  useEffect(() => {
    if (!apiHabilitada || !usuario) {
      setChats([])
      return
    }
    const cargar = () => {
      if (document.visibilityState === 'hidden') return
      misChats().then((cs) => setChats(cs.filter((c) => c.no_leidos > 0))).catch(() => {})
    }
    cargar()
    const id = window.setInterval(cargar, INTERVALO_MS)
    window.addEventListener(EVENTO_CHAT_LEIDO, cargar)
    document.addEventListener('visibilitychange', cargar)
    return () => {
      window.clearInterval(id)
      window.removeEventListener(EVENTO_CHAT_LEIDO, cargar)
      document.removeEventListener('visibilitychange', cargar)
    }
  }, [usuario])

  return {
    chats,
    porProyecto: Object.fromEntries(chats.filter((c) => c.tipo === 'proyecto').map((c) => [c.proyecto_id, c.no_leidos])),
    porSolicitud: Object.fromEntries(chats.filter((c) => c.solicitud_id).map((c) => [c.solicitud_id, c.no_leidos])),
    total: chats.reduce((suma, c) => suma + c.no_leidos, 0),
  }
}
