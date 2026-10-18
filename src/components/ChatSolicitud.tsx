import { useEffect, useState } from 'react'
import { chatDeSolicitud, obtenerUsuario } from '@/lib/chat'
import { useSesion } from '@/lib/sesion'
import type { Solicitud, Usuario } from '@/lib/types'
import { Chat } from '@/components/Chat'

/**
 * Conversación de una solicitud o invitación, para resolver dudas antes de aceptar.
 * Al responsable le muestra el perfil de la persona; se cierra cuando la solicitud se decide.
 */
export function ChatSolicitud({ solicitud }: { solicitud: Solicitud }) {
  const { usuario } = useSesion()
  const soyResponsable = usuario?.id !== solicitud.usuario_id
  const [persona, setPersona] = useState<Omit<Usuario, 'email'> | null>(null)

  useEffect(() => {
    if (!soyResponsable) return
    obtenerUsuario(solicitud.usuario_id).then(setPersona).catch(() => setPersona(null))
  }, [soyResponsable, solicitud.usuario_id])

  const pendiente = solicitud.estado === 'pendiente'

  return (
    <Chat
      id={`solicitud-${solicitud.id}`}
      clave={solicitud.id}
      crearApi={() => chatDeSolicitud(solicitud.id)}
      titulo={soyResponsable ? `Conversación con ${solicitud.usuario_nombre}` : 'Conversación con el responsable del proyecto'}
      descripcion={`Sobre «${solicitud.proyecto_titulo}». Solo la ven ustedes dos.`}
      encabezado={soyResponsable && persona && <PerfilBreve persona={persona} />}
      cerrada={pendiente ? undefined : `La ${solicitud.tipo === 'solicitud' ? 'solicitud' : 'invitación'} ya fue ${solicitud.estado}; la conversación queda como historial.`}
      vacio={soyResponsable
        ? 'Pregúntale lo que necesites saber antes de decidir.'
        : 'Escríbele al responsable si tienes dudas sobre el proyecto o quieres contar más de ti.'}
      alto="h-64"
    />
  )
}

function PerfilBreve({ persona }: { persona: Omit<Usuario, 'email'> }) {
  const etiquetas = [...persona.habilidades, ...persona.intereses]
  return (
    <div className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-slate-600 dark:bg-slate-800/60 dark:text-slate-300">
      <p className="font-medium text-slate-800 dark:text-slate-100">
        <span className="capitalize">{persona.rol}</span>{persona.programa && ` · ${persona.programa}`}
      </p>
      {persona.bio && <p className="mt-1">{persona.bio}</p>}
      {etiquetas.length > 0 && (
        <ul className="mt-2 flex flex-wrap gap-1">
          {etiquetas.map((e) => (
            <li key={e} className="rounded-full bg-white px-2 py-0.5 ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700">{e}</li>
          ))}
        </ul>
      )}
      {!persona.bio && etiquetas.length === 0 && <p className="mt-1">Aún no completó su perfil: puedes preguntarle por el chat.</p>}
    </div>
  )
}
