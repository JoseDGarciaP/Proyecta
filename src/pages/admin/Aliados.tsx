import { useState } from 'react'
import { Check, X } from 'lucide-react'
import { aliadosAdmin, aprobarAliado, cambiarDocumentoAliado, rechazarAliado, type AliadoAdmin } from '@/lib/aliados'
import { Badge, EmptyState, Skeleton } from '@/components/ui'
import { Aviso, Tarjeta, fechaHora, useCarga } from './comun'

const ESTADOS = [
  { id: 'pendiente', label: 'Pendientes' },
  { id: 'aprobado', label: 'Aprobados' },
  { id: 'rechazado', label: 'Rechazados' },
  { id: '', label: 'Todos' },
]

const CLASE: Record<string, string> = {
  pendiente: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  aprobado: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  rechazado: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
}

/** Verificación de aliados externos: aprobar o rechazar con motivo (Ep4-Hu15). */
export function Aliados() {
  const [estado, setEstado] = useState('pendiente')
  const { datos, error, recargar } = useCarga(() => aliadosAdmin(estado), [estado])
  const [mensaje, setMensaje] = useState('')

  const actuar = async (accion: () => Promise<unknown>, ok: string) => {
    setMensaje('')
    try {
      await accion()
      setMensaje(ok)
      await recargar()
    } catch (e) {
      setMensaje((e as Error).message)
    }
  }

  return (
    <Tarjeta titulo="Aliados externos" descripcion="Un aliado nuevo no puede ingresar hasta que lo apruebes. Al rechazarlo, el motivo le llega por correo."
      extra={
        <select className="input" value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado">
          {ESTADOS.map((e) => <option key={e.id} value={e.id}>{e.label}</option>)}
        </select>
      }>
      <Aviso>{error}</Aviso>
      {mensaje && <p className="mb-3 text-sm text-slate-600 dark:text-slate-300" role="status">{mensaje}</p>}
      {!datos ? <Skeleton className="h-32" /> : datos.length === 0 ? (
        <EmptyState titulo="Nada por aquí" detalle={estado === 'pendiente' ? 'No hay aliados esperando aprobación.' : 'No hay aliados en este estado.'} />
      ) : (
        <ul className="divide-y divide-slate-200 dark:divide-slate-800">
          {datos.map((a) => <FilaAliado key={a.usuario_id} a={a} actuar={actuar} />)}
        </ul>
      )}
    </Tarjeta>
  )
}

function FilaAliado({ a, actuar }: { a: AliadoAdmin; actuar: (f: () => Promise<unknown>, ok: string) => Promise<void> }) {
  const [rechazando, setRechazando] = useState(false)
  const [motivo, setMotivo] = useState('')
  const [documento, setDocumento] = useState(a.documento ?? '')
  return (
    <li className="space-y-2 py-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-medium text-slate-900 dark:text-white">{a.razon_social || a.nombre} <Badge className={CLASE[a.estado]}>{a.estado}</Badge></p>
          <p className="text-sm text-slate-500 dark:text-slate-400">{a.nombre} · {a.email} · {a.telefono || 'sin teléfono'}</p>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {a.tipo} · {a.sector || 'sin sector'} · NIT/cédula {a.documento || '—'} · registrado {fechaHora.format(new Date(a.creado_en))}
          </p>
          {a.motivo_rechazo && <p className="text-sm text-rose-600 dark:text-rose-400">Motivo del rechazo: {a.motivo_rechazo}</p>}
        </div>
        {a.estado !== 'aprobado' && (
          <div className="flex gap-2">
            <button type="button" className="btn-primary" onClick={() => actuar(() => aprobarAliado(a.usuario_id), `Aprobaste a ${a.razon_social || a.nombre}.`)}>
              <Check size={15} aria-hidden /> Aprobar
            </button>
            {a.estado === 'pendiente' && (
              <button type="button" className="btn-ghost" onClick={() => setRechazando((v) => !v)}>
                <X size={15} aria-hidden /> Rechazar
              </button>
            )}
          </div>
        )}
      </div>
      {rechazando && (
        <form className="flex flex-wrap gap-2" onSubmit={(e) => {
          e.preventDefault()
          void actuar(() => rechazarAliado(a.usuario_id, motivo), `Rechazaste a ${a.razon_social || a.nombre}.`)
        }}>
          <input className="input flex-1" required minLength={5} placeholder="Motivo (se le envía al aliado)" value={motivo}
            onChange={(e) => setMotivo(e.target.value)} />
          <button className="btn-primary">Confirmar rechazo</button>
        </form>
      )}
      <form className="flex flex-wrap items-center gap-2 text-sm" onSubmit={(e) => {
        e.preventDefault()
        void actuar(() => cambiarDocumentoAliado(a.usuario_id, documento), 'Documento actualizado.')
      }}>
        <label className="text-slate-500 dark:text-slate-400" htmlFor={`doc-${a.usuario_id}`}>Cambiar NIT o cédula</label>
        <input id={`doc-${a.usuario_id}`} className="input w-48" minLength={5} value={documento} onChange={(e) => setDocumento(e.target.value)} />
        <button className="btn-ghost" disabled={documento === (a.documento ?? '')}>Guardar</button>
      </form>
    </li>
  )
}
