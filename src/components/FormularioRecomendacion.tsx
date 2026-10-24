import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useParametrosColaboracion } from '@/lib/parametros'
import { listaATexto, textoALista } from '@/lib/colaboracion'
import type { Recomendacion } from '@/lib/types'

const TEXTOS = {
  solicitud: {
    rol: 'Rol o tipo de aporte que ofreces',
    aporte: 'Qué puedes aportar concretamente',
    aporteAyuda: 'Tareas que puedes asumir, entregables, experiencia relacionada.',
    habilidades: 'Tus habilidades relacionadas (separadas por coma)',
    horas: 'Horas por semana que puedes dedicar',
    motivacion: 'Por qué te interesa este proyecto',
    boton: 'Enviar solicitud',
  },
  invitacion: {
    rol: 'Rol que le propones',
    aporte: 'Qué esperas que aporte',
    aporteAyuda: 'Tareas o resultados que asumiría en el equipo.',
    habilidades: 'Habilidades que valoras de su perfil (separadas por coma)',
    horas: 'Horas por semana que se esperan',
    motivacion: 'Por qué la invitas',
    boton: 'Enviar invitación',
  },
}

/**
 * Formato fijo para pedir unirse a un proyecto o invitar a alguien. Así todas las propuestas
 * llegan con la misma información y el responsable (o el invitado) puede comparar y decidir.
 */
export function FormularioRecomendacion({
  modo, inicial, alEnviar, alCancelar,
}: {
  modo: 'solicitud' | 'invitacion'
  inicial?: Partial<Recomendacion>
  alEnviar: (r: Recomendacion) => Promise<void>
  alCancelar?: () => void
}) {
  const t = TEXTOS[modo]
  const parametros = useParametrosColaboracion()
  const [tipo, setTipo] = useState<number | ''>(inicial?.tipo_aporte_id ?? '')
  const [aporte, setAporte] = useState(inicial?.aporte ?? '')
  const [habilidades, setHabilidades] = useState(listaATexto(inicial?.habilidades ?? []))
  const [horas, setHoras] = useState(String(inicial?.disponibilidad_horas ?? ''))
  const [motivacion, setMotivacion] = useState(inicial?.motivacion ?? '')
  const [mensaje, setMensaje] = useState(inicial?.mensaje ?? '')
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const tipoElegido = parametros?.tipos_aporte.find((x) => x.id === tipo)

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (tipo === '') return setError('Elige el rol o tipo de aporte.')
    setEnviando(true)
    setError('')
    try {
      await alEnviar({
        tipo_aporte_id: tipo,
        aporte: aporte.trim(),
        habilidades: textoALista(habilidades),
        disponibilidad_horas: Number(horas),
        motivacion: motivacion.trim(),
        mensaje: mensaje.trim(),
      })
    } catch (err) {
      setError((err as Error).message)
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="space-y-3">
      <div>
        <label className="label" htmlFor="reco-tipo">{t.rol}</label>
        <select id="reco-tipo" className="input" required value={tipo} onChange={(e) => setTipo(e.target.value ? Number(e.target.value) : '')}>
          <option value="">{parametros ? 'Elige una opción' : 'Cargando…'}</option>
          {parametros?.tipos_aporte.map((x) => <option key={x.id} value={x.id}>{x.nombre}</option>)}
        </select>
        {tipoElegido?.descripcion && <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{tipoElegido.descripcion}</p>}
      </div>
      <div>
        <label className="label" htmlFor="reco-aporte">{t.aporte}</label>
        <textarea id="reco-aporte" className="input min-h-20" required minLength={10} maxLength={1000}
          value={aporte} onChange={(e) => setAporte(e.target.value)} placeholder={t.aporteAyuda} />
      </div>
      <div className="grid gap-3 sm:grid-cols-[1fr_9rem]">
        <div>
          <label className="label" htmlFor="reco-habilidades">{t.habilidades}</label>
          <input id="reco-habilidades" className="input" value={habilidades} onChange={(e) => setHabilidades(e.target.value)}
            placeholder="Python, encuestas, SIG" />
        </div>
        <div>
          <label className="label" htmlFor="reco-horas">Horas/semana</label>
          <input id="reco-horas" type="number" className="input tabular-nums" required min={1} max={60}
            value={horas} onChange={(e) => setHoras(e.target.value)} aria-describedby="reco-horas-ayuda" />
          <p id="reco-horas-ayuda" className="sr-only">{t.horas}</p>
        </div>
      </div>
      <div>
        <label className="label" htmlFor="reco-motivacion">{t.motivacion}</label>
        <textarea id="reco-motivacion" className="input min-h-16" required minLength={10} maxLength={1000}
          value={motivacion} onChange={(e) => setMotivacion(e.target.value)} />
      </div>
      <div>
        <label className="label" htmlFor="reco-mensaje">Nota adicional <span className="font-normal text-slate-400">(opcional)</span></label>
        <input id="reco-mensaje" className="input" maxLength={1000} value={mensaje} onChange={(e) => setMensaje(e.target.value)} />
      </div>
      {error && <p className="text-sm text-rose-600">{error}</p>}
      <div className="flex flex-wrap gap-2 pt-1">
        <button className="btn-primary" disabled={enviando}>
          {enviando && <Loader2 size={15} className="animate-spin" aria-hidden />} {t.boton}
        </button>
        {alCancelar && <button type="button" className="btn-ghost" onClick={alCancelar}>Cancelar</button>}
      </div>
    </form>
  )
}
