import { useState, type ReactNode } from 'react'
import { ArrowDown, ArrowUp, Pencil, Plus, Trash2 } from 'lucide-react'
import { motivos as apiMotivos, plantillas as apiPlantillas, tiposAporte as apiTipos } from '@/lib/admin'
import { invalidarParametros } from '@/lib/parametros'
import type { Motivo, ParaPlantilla, Plantilla, TipoAporte, TipoMotivo } from '@/lib/types'
import { Badge, Skeleton } from '@/components/ui'
import { Modal } from '@/components/Modal'
import { useConfirmar } from '@/components/Confirmar'
import { Aviso, BotonGuardar, Interruptor, Tarjeta, useCarga } from './comun'

type Api<T extends { id: number }> = {
  listar: () => Promise<T[]>
  crear: (d: Omit<T, 'id'>) => Promise<T>
  editar: (id: number, d: Omit<T, 'id'>) => Promise<T>
  eliminar: (id: number) => Promise<void>
}

/** Motivos de decisión, tipos de aporte y plantillas de mensaje: lo que usa el flujo de colaboración. */
export function Colaboracion() {
  // Una sola carga para las dos listas: un motivo puede pasar de aprobación a rechazo al editarlo.
  const motivos = useCarga(apiMotivos.listar)
  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <ListaMotivos tipo="aprobacion" datos={motivos.datos} recargar={motivos.recargar} />
        <ListaMotivos tipo="rechazo" datos={motivos.datos} recargar={motivos.recargar} />
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <ListaTipos />
        <ListaPlantillas />
      </div>
    </div>
  )
}

/** Lista editable común: activar/desactivar, reordenar, editar y eliminar. */
function ListaEditable<T extends { id: number; activo: boolean; orden: number }>({
  api, items, recargar, nombre, detalle, formulario, nuevo, titulo, descripcion, etiqueta,
}: {
  api: Api<T>
  items: T[] | null
  recargar: () => void
  nombre: (x: T) => string
  detalle: (x: T) => ReactNode
  formulario: (x: Omit<T, 'id'>, set: (x: Omit<T, 'id'>) => void) => ReactNode
  nuevo: () => Omit<T, 'id'>
  titulo: string
  descripcion: string
  etiqueta: string
}) {
  const [editando, setEditando] = useState<{ id: number | null; datos: Omit<T, 'id'> } | null>(null)
  const [error, setError] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const { confirmar, ventana } = useConfirmar()

  const sinId = (x: T): Omit<T, 'id'> => {
    const { id: _id, ...resto } = x
    return resto
  }

  const hecho = () => {
    invalidarParametros()
    recargar()
  }

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editando) return
    setOcupado(true)
    setError('')
    try {
      if (editando.id === null) await api.crear(editando.datos)
      else await api.editar(editando.id, editando.datos)
      setEditando(null)
      hecho()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setOcupado(false)
    }
  }

  const actualizar = async (x: T, cambios: Partial<T>) => {
    setError('')
    try {
      await api.editar(x.id, { ...sinId(x), ...cambios })
      hecho()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const mover = async (i: number, dir: -1 | 1) => {
    if (!items) return
    const a = items[i], b = items[i + dir]
    if (!b) return
    // Se renumeran ambos para que el orden quede explícito aunque tuvieran el mismo valor.
    await Promise.all([api.editar(a.id, { ...sinId(a), orden: i + dir }), api.editar(b.id, { ...sinId(b), orden: i })]).catch((e) => setError(e.message))
    hecho()
  }

  const eliminar = async (x: T) => {
    if (!(await confirmar({
      titulo: `¿Eliminar «${nombre(x)}»?`,
      detalle: 'Las solicitudes que ya lo usaron conservan el texto. Si solo quieres dejar de ofrecerlo, desactívalo.',
      aceptar: 'Eliminar', peligro: true,
    }))) return
    try {
      await api.eliminar(x.id)
      hecho()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <Tarjeta titulo={titulo} descripcion={descripcion} extra={
      <button className="btn-ghost text-xs" onClick={() => setEditando({ id: null, datos: { ...nuevo(), orden: items?.length ?? 0 } })}>
        <Plus size={14} aria-hidden /> Agregar
      </button>
    }>
      {ventana}
      <Aviso>{error}</Aviso>
      {!items ? <Skeleton className="h-40" /> : items.length === 0 ? (
        <p className="text-sm text-slate-500">No hay elementos. Agrega el primero.</p>
      ) : (
        <ul className="divide-y divide-slate-200 dark:divide-slate-800">
          {items.map((x, i) => (
            <li key={x.id} className={`flex items-start gap-3 py-2.5 ${x.activo ? '' : 'opacity-55'}`}>
              <div className="flex flex-col pt-0.5">
                <button className="text-slate-400 hover:text-slate-700 disabled:opacity-30 dark:hover:text-slate-200" disabled={i === 0} onClick={() => mover(i, -1)} aria-label="Subir"><ArrowUp size={13} /></button>
                <button className="text-slate-400 hover:text-slate-700 disabled:opacity-30 dark:hover:text-slate-200" disabled={i === items.length - 1} onClick={() => mover(i, 1)} aria-label="Bajar"><ArrowDown size={13} /></button>
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-900 dark:text-white">{nombre(x)}</p>
                <div className="text-xs text-slate-500 dark:text-slate-400">{detalle(x)}</div>
              </div>
              <Interruptor activo={x.activo} etiqueta={`${nombre(x)} activo`} alCambiar={(activo) => actualizar(x, { activo } as Partial<T>)} />
              <button className="rounded p-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-100" onClick={() => setEditando({ id: x.id, datos: sinId(x) })} aria-label={`Editar ${nombre(x)}`}><Pencil size={14} /></button>
              <button className="rounded p-1 text-slate-500 hover:text-rose-600" onClick={() => eliminar(x)} aria-label={`Eliminar ${nombre(x)}`}><Trash2 size={14} /></button>
            </li>
          ))}
        </ul>
      )}
      {editando && (
        <Modal titulo={editando.id === null ? `Agregar ${etiqueta}` : `Editar ${etiqueta}`} alCerrar={() => setEditando(null)}>
          <form onSubmit={guardar} className="space-y-3">
            {formulario(editando.datos, (datos) => setEditando({ ...editando, datos }))}
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" className="h-4 w-4 accent-brand-600" checked={editando.datos.activo}
                onChange={(e) => setEditando({ ...editando, datos: { ...editando.datos, activo: e.target.checked } })} />
              Activo (se ofrece en los formularios)
            </label>
            <Aviso>{error}</Aviso>
            <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={() => setEditando(null)}>Cancelar</button><BotonGuardar ocupado={ocupado} /></div>
          </form>
        </Modal>
      )}
    </Tarjeta>
  )
}

function ListaMotivos({ tipo, datos, recargar }: { tipo: TipoMotivo; datos: Motivo[] | null; recargar: () => void }) {
  const aprobar = tipo === 'aprobacion'
  return (
    <ListaEditable<Motivo>
      api={apiMotivos}
      items={datos?.filter((m) => m.tipo === tipo) ?? null}
      recargar={recargar}
      titulo={aprobar ? 'Motivos para aprobar' : 'Motivos para rechazar'}
      descripcion={aprobar ? 'Quien aprueba una colaboración debe elegir uno.' : 'Quien rechaza debe elegir uno; la otra persona lo recibe por correo.'}
      etiqueta="motivo"
      nombre={(m) => m.nombre}
      detalle={(m) => <>{m.descripcion}{m.requiere_comentario && <Badge className="ml-1 bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">pide comentario</Badge>}</>}
      nuevo={() => ({ tipo, nombre: '', descripcion: '', requiere_comentario: false, activo: true, orden: 0 })}
      formulario={(m, set) => (
        <>
          <label className="block"><span className="label">Motivo</span>
            <input className="input" required minLength={3} maxLength={150} value={m.nombre} onChange={(e) => set({ ...m, nombre: e.target.value })} /></label>
          <label className="block"><span className="label">Descripción <span className="font-normal text-slate-400">(ayuda a elegir)</span></span>
            <textarea className="input min-h-16" maxLength={500} value={m.descripcion} onChange={(e) => set({ ...m, descripcion: e.target.value })} /></label>
          <label className="block"><span className="label">Tipo</span>
            <select className="input" value={m.tipo} onChange={(e) => set({ ...m, tipo: e.target.value as TipoMotivo })}>
              <option value="aprobacion">Aprobación</option><option value="rechazo">Rechazo</option>
            </select></label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" className="h-4 w-4 accent-brand-600" checked={m.requiere_comentario} onChange={(e) => set({ ...m, requiere_comentario: e.target.checked })} />
            Exigir comentario al elegirlo (útil para «Otro motivo»)
          </label>
        </>
      )}
    />
  )
}

function ListaTipos() {
  const { datos, recargar } = useCarga(apiTipos.listar)
  return (
    <ListaEditable<TipoAporte>
      api={apiTipos}
      items={datos}
      recargar={recargar}
      titulo="Tipos de aporte"
      descripcion="Roles que se eligen al solicitar unirse o al invitar."
      etiqueta="tipo de aporte"
      nombre={(t) => t.nombre}
      detalle={(t) => t.descripcion}
      nuevo={() => ({ nombre: '', descripcion: '', activo: true, orden: 0 })}
      formulario={(t, set) => (
        <>
          <label className="block"><span className="label">Nombre</span>
            <input className="input" required minLength={3} maxLength={120} value={t.nombre} onChange={(e) => set({ ...t, nombre: e.target.value })} /></label>
          <label className="block"><span className="label">Descripción</span>
            <textarea className="input min-h-16" maxLength={500} value={t.descripcion} onChange={(e) => set({ ...t, descripcion: e.target.value })} /></label>
        </>
      )}
    />
  )
}

const PARA: Record<ParaPlantilla, string> = { solicitante: 'Quien solicita', responsable: 'Responsable', todos: 'Ambos' }

function ListaPlantillas() {
  const { datos, recargar } = useCarga(apiPlantillas.listar)
  return (
    <ListaEditable<Plantilla>
      api={apiPlantillas}
      items={datos}
      recargar={recargar}
      titulo="Plantillas de mensaje"
      descripcion="Mensajes tipo para la conversación de una solicitud. Usa [corchetes] para lo que hay que completar."
      etiqueta="plantilla"
      nombre={(p) => p.titulo}
      detalle={(p) => <><Badge className="mr-1 bg-accent-100 text-accent-800 dark:bg-accent-500/15 dark:text-accent-300">{PARA[p.para]}</Badge><span className="line-clamp-2">{p.texto}</span></>}
      nuevo={() => ({ titulo: '', texto: '', para: 'todos', activo: true, orden: 0 })}
      formulario={(p, set) => (
        <>
          <label className="block"><span className="label">Título</span>
            <input className="input" required minLength={3} maxLength={120} value={p.titulo} onChange={(e) => set({ ...p, titulo: e.target.value })} /></label>
          <label className="block"><span className="label">Texto</span>
            <textarea className="input min-h-28" required minLength={5} maxLength={2000} value={p.texto} onChange={(e) => set({ ...p, texto: e.target.value })} /></label>
          <label className="block"><span className="label">La ve</span>
            <select className="input" value={p.para} onChange={(e) => set({ ...p, para: e.target.value as ParaPlantilla })}>
              {Object.entries(PARA).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select></label>
        </>
      )}
    />
  )
}
