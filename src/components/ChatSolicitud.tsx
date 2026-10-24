import { useEffect, useState } from 'react'
import { chatDeSolicitud, obtenerUsuario } from '@/lib/chat'
import { useParametrosColaboracion } from '@/lib/parametros'
import { useSesion } from '@/lib/sesion'
import type { Solicitud, Usuario } from '@/lib/types'
import { Chat } from '@/components/Chat'
import { FichaRecomendacion } from '@/components/FichaRecomendacion'
import { InsigniasDe, NivelDe } from '@/components/Insignia'
import { usePuede } from '@/lib/permisos'

/**
 * Conversación de una solicitud o invitación, para resolver dudas antes de aceptar.
 * Arriba muestra la propuesta en formato fijo y, al responsable, el perfil de la persona;
 * ofrece plantillas de mensaje según quién escribe. Se cierra cuando la solicitud se decide.
 */
export function ChatSolicitud({ solicitud, conFicha = true }: { solicitud: Solicitud; conFicha?: boolean }) {
  const { usuario } = useSesion()
  const parametros = useParametrosColaboracion()
  const soyResponsable = usuario?.id !== solicitud.usuario_id
  const [persona, setPersona] = useState<Omit<Usuario, 'email'> | null>(null)

  useEffect(() => {
    if (!soyResponsable) return
    obtenerUsuario(solicitud.usuario_id).then(setPersona).catch(() => setPersona(null))
  }, [soyResponsable, solicitud.usuario_id])

  const puede = usePuede()
  const pendiente = solicitud.estado === 'pendiente'
  const miPapel = soyResponsable ? 'responsable' : 'solicitante'
  const plantillas = parametros?.plantillas.filter((p) => p.para === 'todos' || p.para === miPapel) ?? []

  return (
    <Chat
      id={`solicitud-${solicitud.id}`}
      clave={solicitud.id}
      crearApi={() => chatDeSolicitud(solicitud.id)}
      titulo={soyResponsable ? `Conversación con ${solicitud.usuario_nombre}` : 'Conversación con el responsable del proyecto'}
      descripcion={`Sobre «${solicitud.proyecto_titulo}». Solo la ven ustedes dos.`}
      encabezado={
        <div className="mt-3 space-y-2">
          {conFicha && (
            <details open={pendiente}>
              <summary className="cursor-pointer text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200">
                {solicitud.tipo === 'solicitud' ? 'Propuesta de colaboración' : 'Propuesta de la invitación'}
              </summary>
              <div className="mt-2"><FichaRecomendacion solicitud={solicitud} /></div>
            </details>
          )}
          {soyResponsable && persona && <PerfilBreve persona={persona} id={solicitud.usuario_id} />}
        </div>
      }
      cerrada={!puede('chat.usar') ? 'Tu rol no tiene permiso para escribir en los chats.' : pendiente ? undefined : `La ${solicitud.tipo === 'solicitud' ? 'solicitud' : 'invitación'} ya fue ${solicitud.estado}; la conversación queda como historial.`}
      vacio={soyResponsable
        ? 'Pregúntale lo que necesites saber antes de decidir. Puedes partir de una plantilla.'
        : 'Escríbele al responsable si tienes dudas sobre el proyecto o quieres contar más de ti.'}
      alto="h-64"
      plantillas={pendiente ? plantillas : []}
    />
  )
}

function PerfilBreve({ persona, id }: { persona: Omit<Usuario, 'email'>; id: string }) {
  const etiquetas = [...persona.habilidades, ...persona.intereses]
  return (
    <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600 dark:bg-slate-800/60 dark:text-slate-300">
      <p className="font-medium text-slate-800 dark:text-slate-100">
        {persona.rol_nombre}{persona.programa && ` · ${persona.programa}`} <NivelDe usuarioId={id} /> <InsigniasDe usuarioId={id} max={6} />
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
