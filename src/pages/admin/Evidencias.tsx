import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, X } from 'lucide-react'
import { ESTADO_EVIDENCIA, TIPO_EVIDENCIA, adminEvidencias, listarAcciones, olvidarNivel } from '@/lib/experiencia'
import type { EstadoEvidencia, Evidencia } from '@/lib/types'
import { Badge, Skeleton } from '@/components/ui'
import { VerArchivo, tamano } from '@/components/Evidencias'
import { NombrePersona } from '@/components/Insignia'
import { Aviso, Tarjeta, fechaHora, useCarga } from './comun'

const FILTROS: [EstadoEvidencia | '', string][] = [['pendiente', 'Por revisar'], ['aprobada', 'Aprobadas'], ['rechazada', 'Rechazadas'], ['', 'Todas']]

/** Revisión de certificados y evidencias: aprobar con la XP que se decida, o rechazar con un motivo. */
export function EvidenciasAdmin() {
  const [estado, setEstado] = useState<EstadoEvidencia | ''>('pendiente')
  const lista = useCarga(() => adminEvidencias.listar(estado || undefined), [estado])
  const sugerida = useCarga(() => listarAcciones().then((as) => as.find((a) => a.clave === 'evidencia_aprobada')?.puntos ?? 30))
  const [error, setError] = useState('')

  return (
    <Tarjeta
      titulo="Certificados y evidencias"
      descripcion="Lo que las personas suben desde su perfil o desde un proyecto. Al aprobar, decides cuánta experiencia otorgar (el valor sugerido se cambia en «Niveles y XP»)."
      extra={
        <div role="tablist" className="inline-flex rounded-lg bg-slate-100 p-0.5 dark:bg-slate-800">
          {FILTROS.map(([v, texto]) => (
            <button key={texto} role="tab" aria-selected={estado === v} onClick={() => setEstado(v)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium ${estado === v
                ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-950 dark:text-white' : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}`}>
              {texto}
            </button>
          ))}
        </div>
      }
    >
      <Aviso>{lista.error || error}</Aviso>
      {!lista.datos ? <Skeleton className="h-40" /> : lista.datos.length === 0 ? (
        <p className="py-6 text-center text-sm text-slate-500">{estado === 'pendiente' ? 'No hay evidencias por revisar.' : 'Sin evidencias.'}</p>
      ) : (
        <ul className="divide-y divide-slate-100 dark:divide-slate-800">
          {lista.datos.map((e) => (
            <FilaEvidencia key={e.id} e={e} sugerida={sugerida.datos ?? 30} alError={setError}
              alRevisar={(nueva) => {
                olvidarNivel(nueva.usuario_id)
                lista.setDatos((xs) => (estado === 'pendiente' ? xs?.filter((x) => x.id !== nueva.id) : xs?.map((x) => (x.id === nueva.id ? nueva : x))) ?? null)
              }} />
          ))}
        </ul>
      )}
    </Tarjeta>
  )
}

function FilaEvidencia({ e, sugerida, alRevisar, alError }: {
  e: Evidencia; sugerida: number; alRevisar: (e: Evidencia) => void; alError: (m: string) => void
}) {
  const [puntos, setPuntos] = useState(String(sugerida))
  const [comentario, setComentario] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const [estadoTexto, estadoClase] = ESTADO_EVIDENCIA[e.estado]

  const revisar = async (aprobar: boolean) => {
    if (!aprobar && comentario.trim().length < 3) {
      setError('Escribe el motivo del rechazo; la persona lo verá.')
      return
    }
    setOcupado(true)
    setError('')
    try {
      alRevisar(await adminEvidencias.revisar(e.id, aprobar, aprobar ? Number(puntos) || 0 : null, comentario.trim()))
    } catch (err) {
      setError((err as Error).message)
      setOcupado(false)
    }
  }

  return (
    <li className="py-4">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-center gap-1.5 text-sm font-medium text-slate-900 dark:text-white">
            {e.titulo}
            <Badge className="bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{TIPO_EVIDENCIA[e.tipo]}</Badge>
            <Badge className={estadoClase}>{estadoTexto}</Badge>
            {e.estado === 'aprobada' && <Badge className="bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300">+{e.xp_otorgada} XP</Badge>}
          </p>
          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            <NombrePersona id={e.usuario_id} nombre={e.usuario_nombre} className="font-medium" />
            {e.proyecto_id && <> · <Link to={`/proyectos/${e.proyecto_id}`} className="hover:underline">{e.proyecto_titulo}</Link></>}
            {' · '}{fechaHora.format(new Date(e.creado_en))} · {e.archivo_nombre} ({tamano(e.archivo_tamano)})
          </p>
          {e.descripcion && <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{e.descripcion}</p>}
          {e.estado !== 'pendiente' && (e.comentario || e.revisada_por) && (
            <p className="mt-1 text-xs text-slate-500">
              Revisada por {e.revisada_por ?? '—'}{e.revisada_en && ` el ${fechaHora.format(new Date(e.revisada_en))}`}{e.comentario && `: «${e.comentario}»`}
            </p>
          )}
        </div>
        <VerArchivo e={e} alError={alError} />
      </div>

      {e.estado === 'pendiente' && (
        <div className="mt-3 flex flex-wrap items-end gap-2 rounded-lg bg-slate-50 p-3 dark:bg-slate-900">
          <label className="block">
            <span className="label">XP a otorgar</span>
            <input type="number" min={0} max={10000} className="input w-24 py-1.5 tabular-nums" value={puntos} onChange={(ev) => setPuntos(ev.target.value)} />
          </label>
          <label className="block min-w-48 flex-1">
            <span className="label">Comentario (obligatorio si rechazas)</span>
            <input className="input py-1.5" maxLength={1000} value={comentario} onChange={(ev) => setComentario(ev.target.value)}
              placeholder="¡Buen trabajo! / El archivo no es legible…" />
          </label>
          <button className="btn bg-emerald-600 py-1.5 text-white hover:bg-emerald-700" disabled={ocupado} onClick={() => revisar(true)}>
            <Check size={15} aria-hidden /> Aprobar
          </button>
          <button className="btn-ghost py-1.5 text-rose-700 dark:text-rose-400" disabled={ocupado} onClick={() => revisar(false)}>
            <X size={15} aria-hidden /> Rechazar
          </button>
          {error && <p className="basis-full text-sm text-rose-600">{error}</p>}
        </div>
      )}
    </li>
  )
}
