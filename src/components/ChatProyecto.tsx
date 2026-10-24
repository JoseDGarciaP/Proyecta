import { chatDeProyecto } from '@/lib/chat'
import { apiHabilitada } from '@/lib/http'
import type { Proyecto } from '@/lib/types'
import { Chat } from '@/components/Chat'
import { usePuede } from '@/lib/permisos'

/** Chat del equipo: responsable y miembros (con la API conectada). Quien no hace parte no lo ve. */
export function ChatProyecto({ proyecto }: { proyecto: Proyecto }) {
  const puede = usePuede()
  if (!apiHabilitada) return null
  return (
    <Chat
      id="chat"
      clave={proyecto.id}
      crearApi={() => chatDeProyecto(proyecto.id)}
      titulo="Chat del equipo"
      descripcion="Solo lo ven quien registró el proyecto y sus colaboradores."
      vacio="Aún no hay mensajes. Escribe el primero para coordinar con el equipo."
      cerrada={puede('chat.usar') ? undefined : 'Tu rol no tiene permiso para escribir en los chats.'}
    />
  )
}
