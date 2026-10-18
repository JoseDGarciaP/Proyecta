import { chatDeProyecto } from '@/lib/chat'
import { apiHabilitada } from '@/lib/http'
import type { Proyecto } from '@/lib/types'
import { Chat } from '@/components/Chat'

/** Chat del equipo: responsable y miembros (con la API conectada). Quien no hace parte no lo ve. */
export function ChatProyecto({ proyecto }: { proyecto: Proyecto }) {
  if (!apiHabilitada) return null
  return (
    <Chat
      id="chat"
      clave={proyecto.id}
      crearApi={() => chatDeProyecto(proyecto.id)}
      titulo="Chat del equipo"
      descripcion="Solo lo ven quien registró el proyecto y sus colaboradores."
      vacio="Aún no hay mensajes. Escribe el primero para coordinar con el equipo."
    />
  )
}
