import { useState } from 'react'
import { Check, Loader2, X } from 'lucide-react'
import { decidirSolicitud } from '@/lib/colaboracion'
import { useParametrosColaboracion } from '@/lib/parametros'
import type { Solicitud } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { FichaRecomendacion } from '@/components/FichaRecomendacion'

/** Ventana para aprobar o rechazar con un motivo del catálogo (obligatorio) y un comentario. */
export function DecidirSolicitud({
  solicitud, accion, alCerrar, alDecidir,
}: { solicitud: Solicitud; accion: 'aceptar' | 'rechazar'; alCerrar: () => void; alDecidir: (s: Solicitud) => void }) {
  const parametros = useParametrosColaboracion()
  const aprobar = accion === 'aceptar'
  const motivos = parametros?.motivos.filter((m) => m.tipo === (aprobar ? 'aprobacion' : 'rechazo')) ?? []
  const [motivoId, setMotivoId] = useState<number | null>(null)
  const [comentario, setComentario] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const motivo = motivos.find((m) => m.id === motivoId)
  const faltaComentario = Boolean(motivo?.requiere_comentario && !comentario.trim())
  const clase = solicitud.tipo === 'solicitud' ? 'solicitud' : 'invitación'
  const quien = solicitud.tipo === 'solicitud' ? solicitud.usuario_nombre : 'el responsable del proyecto'

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!motivoId) return setError('Elige un motivo.')
    if (faltaComentario) return setError('Este motivo requiere un comentario.')
    setEnviando(true)
    setError('')
    try {
      alDecidir(await decidirSolicitud(solicitud.id, accion, motivoId, comentario.trim()))
    } catch (err) {
      setError((err as Error).message)
      setEnviando(false)
    }
  }

  return (
    <Modal
      titulo={`${aprobar ? 'Aprobar' : 'Rechazar'} ${clase}`}
      descripcion={<>«{solicitud.proyecto_titulo}». Le avisaremos a {quien} en la plataforma y por correo, con el motivo.</>}
      alCerrar={alCerrar}
      ancho="max-w-xl"
    >
      <form onSubmit={enviar} className="space-y-4">
        <details className="text-sm">
          <summary className="cursor-pointer text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200">
            Ver la propuesta
          </summary>
          <div className="mt-2"><FichaRecomendacion solicitud={solicitud} conDecision={false} /></div>
        </details>

        <fieldset>
          <legend className="label">Motivo <span className="text-rose-600">*</span></legend>
          {!parametros ? (
            <p className="text-sm text-slate-500">Cargando motivos…</p>
          ) : motivos.length === 0 ? (
            <p className="text-sm text-amber-700">No hay motivos activos. Pídele a un administrador que los configure.</p>
          ) : (
            <div className="space-y-1.5">
              {motivos.map((m) => (
                <label key={m.id} className={`flex cursor-pointer gap-3 rounded-md border px-3 py-2 text-sm transition ${motivoId === m.id
                  ? (aprobar ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-500/10' : 'border-rose-500 bg-rose-50 dark:bg-rose-500/10')
                  : 'border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/60'}`}>
                  <input type="radio" name="motivo" className="mt-1 accent-brand-600" checked={motivoId === m.id} onChange={() => setMotivoId(m.id)} />
                  <span>
                    <span className="font-medium text-slate-900 dark:text-white">{m.nombre}</span>
                    {m.descripcion && <span className="block text-xs text-slate-500 dark:text-slate-400">{m.descripcion}</span>}
                  </span>
                </label>
              ))}
            </div>
          )}
        </fieldset>

        <div>
          <label className="label" htmlFor="decision-comentario">
            Comentario {motivo?.requiere_comentario ? <span className="text-rose-600">*</span> : <span className="font-normal text-slate-400">(opcional)</span>}
          </label>
          <textarea id="decision-comentario" className="input min-h-20" maxLength={1000} value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            placeholder={aprobar ? 'Bienvenida, próximos pasos, primera reunión…' : 'Explica con respeto; la otra persona lo leerá.'} />
        </div>

        {error && <p className="text-sm text-rose-600">{error}</p>}
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button>
          <button
            className={aprobar ? 'btn bg-emerald-600 text-white hover:bg-emerald-700' : 'btn bg-rose-600 text-white hover:bg-rose-700'}
            disabled={enviando || !motivoId || faltaComentario}
          >
            {enviando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : aprobar ? <Check size={15} aria-hidden /> : <X size={15} aria-hidden />}
            {aprobar ? 'Aprobar' : 'Rechazar'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
