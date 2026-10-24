import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Check, ExternalLink, Pencil, Plus, Search, Trash2, X } from 'lucide-react'
import { adminPostulaciones } from '@/lib/experiencia'
import type { EstadoPostulacion, Postulacion } from '@/lib/types'
import { EstadoPostulacionBadge } from '@/components/Postulaciones'
import {
  crearActor, crearOportunidad, editarActor, editarOportunidad, eliminarActor, eliminarOportunidad, eliminarProyectoAdmin,
  listarProyectosAdmin, type ActorEntrada, type OportunidadEntrada,
} from '@/lib/admin'
import { listarActores, listarOportunidades } from '@/lib/api'
import { useAreas, useOds } from '@/lib/parametros'
import { TIPOS_ACTOR, type Actor, type Oportunidad, type ProyectoAdmin, type TipoActor } from '@/lib/types'
import { formatCOP, formatDate } from '@/lib/format'
import { EstadoBadge, Skeleton } from '@/components/ui'
import { Modal } from '@/components/Modal'
import { useConfirmar } from '@/components/Confirmar'
import { Aviso, BotonGuardar, useCarga } from './comun'
import { usePuede } from '@/lib/permisos'

const SECCIONES = [['proyectos', 'Proyectos'], ['oportunidades', 'Oportunidades'], ['postulaciones', 'Postulaciones'], ['actores', 'Actores']] as const
type Seccion = (typeof SECCIONES)[number][0]

/** Contenido de la plataforma: retirar proyectos y administrar oportunidades y actores. */
export function Moderacion() {
  const [params] = useSearchParams()
  const [seccion, setSeccion] = useState<Seccion>((SECCIONES.find(([id]) => id === params.get('seccion'))?.[0]) ?? 'proyectos')
  const puede = usePuede()
  const permiso = (id: Seccion) => (id === 'postulaciones' ? 'oportunidades.gestionar' : `${id}.gestionar`)
  const visibles = SECCIONES.filter(([id]) => id === 'proyectos' || puede(permiso(id)))
  return (
    <div className="space-y-4">
      <div className="inline-flex rounded-md border border-slate-200 p-0.5 text-sm dark:border-slate-700" role="group" aria-label="Contenido">
        {visibles.map(([id, label]) => (
          <button key={id} onClick={() => setSeccion(id)} aria-pressed={seccion === id}
            className={`rounded px-3 py-1.5 ${seccion === id ? 'bg-brand-600 text-white dark:bg-brand-300 dark:text-brand-950' : 'text-slate-600 dark:text-slate-300'}`}>
            {label}
          </button>
        ))}
      </div>
      {seccion === 'proyectos' && <Proyectos />}
      {seccion === 'oportunidades' && <Oportunidades />}
      {seccion === 'postulaciones' && <Postulaciones />}
      {seccion === 'actores' && <Actores />}
    </div>
  )
}

function Proyectos() {
  const [q, setQ] = useState('')
  const [buscar, setBuscar] = useState('')
  const { datos, error, recargar } = useCarga(() => listarProyectosAdmin(buscar), [buscar])
  const [retirando, setRetirando] = useState<ProyectoAdmin | null>(null)

  return (
    <div className="space-y-3">
      <form className="relative max-w-md" onSubmit={(e) => { e.preventDefault(); setBuscar(q.trim()) }}>
        <Search size={16} className="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" aria-hidden />
        <input className="input pl-9" placeholder="Título, líder, responsable o correo (Enter)" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Buscar proyectos" />
      </form>
      <Aviso>{error}</Aviso>
      {!datos ? <Skeleton className="h-80" /> : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead className="border-b border-slate-200 text-left text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <tr><th className="px-4 py-3 font-medium">Proyecto</th><th className="px-4 py-3 font-medium">Responsable</th><th className="px-4 py-3 font-medium">Equipo</th><th className="px-4 py-3 font-medium">Estado</th><th /></tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {datos.length === 0 && <tr><td colSpan={5} className="px-4 py-10 text-center text-slate-500">Sin proyectos.</td></tr>}
              {datos.map((p) => (
                <tr key={p.id}>
                  <td className="px-4 py-3">
                    <Link to={`/proyectos/${p.id}`} className="font-medium text-slate-900 hover:text-brand-700 dark:text-white dark:hover:text-brand-300">{p.titulo}</Link>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{p.area} · {formatDate(p.creado_en)}</p>
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {p.responsable_nombre ? <><p className="text-slate-800 dark:text-slate-200">{p.responsable_nombre}</p><p className="text-slate-500">{p.responsable_email}</p></> : <span className="text-slate-400">Sin responsable</span>}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600 tabular-nums dark:text-slate-300">
                    {p.miembros} colaboradores{p.solicitudes_pendientes > 0 && <span className="block text-amber-700 dark:text-amber-400">{p.solicitudes_pendientes} solicitudes pendientes</span>}
                  </td>
                  <td className="px-4 py-3"><EstadoBadge estado={p.estado} /></td>
                  <td className="px-4 py-3 text-right">
                    <button className="btn-ghost text-xs text-rose-700 dark:text-rose-400" onClick={() => setRetirando(p)}><Trash2 size={14} aria-hidden /> Retirar</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {retirando && <RetirarProyecto p={retirando} alCerrar={() => setRetirando(null)} alRetirar={() => { setRetirando(null); void recargar() }} />}
    </div>
  )
}

function RetirarProyecto({ p, alCerrar, alRetirar }: { p: ProyectoAdmin; alCerrar: () => void; alRetirar: () => void }) {
  const [motivo, setMotivo] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  return (
    <Modal titulo={`Retirar «${p.titulo}»`} descripcion="Se elimina con su chat, miembros y solicitudes. No se puede deshacer." alCerrar={alCerrar}>
      <form className="space-y-3" onSubmit={async (e) => {
        e.preventDefault()
        setOcupado(true)
        try {
          await eliminarProyectoAdmin(p.id, motivo.trim())
          alRetirar()
        } catch (err) {
          setError((err as Error).message)
          setOcupado(false)
        }
      }}>
        <label className="block"><span className="label">Motivo <span className="font-normal text-slate-400">(se le envía a {p.responsable_nombre ?? 'quien lo registró'})</span></span>
          <textarea className="input min-h-24" required minLength={5} maxLength={500} value={motivo} onChange={(e) => setMotivo(e.target.value)}
            placeholder="Ej.: Está duplicado con otro proyecto registrado." /></label>
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button>
          <button className="btn bg-rose-600 text-white hover:bg-rose-700" disabled={ocupado || motivo.trim().length < 5}>Retirar proyecto</button>
        </div>
      </form>
    </Modal>
  )
}

const TIPOS_OPORTUNIDAD: Record<Oportunidad['tipo'], string> = {
  convocatoria: 'Convocatoria', financiacion: 'Financiación', mentoria: 'Mentoría', infraestructura: 'Infraestructura',
}

function Oportunidades() {
  const { datos, error, recargar } = useCarga(listarOportunidades)
  const [editando, setEditando] = useState<Oportunidad | 'nueva' | null>(null)
  const [fallo, setFallo] = useState('')
  const { confirmar, ventana } = useConfirmar()
  return (
    <div className="space-y-3">
      {ventana}
      <button className="btn-primary" onClick={() => setEditando('nueva')}><Plus size={15} aria-hidden /> Nueva oportunidad</button>
      <Aviso>{error || fallo}</Aviso>
      {!datos ? <Skeleton className="h-80" /> : (
        <ul className="card divide-y divide-slate-200 dark:divide-slate-800">
          {datos.length === 0 && <li className="px-5 py-10 text-center text-sm text-slate-500">Sin oportunidades.</li>}
          {datos.map((o) => (
            <li key={o.id} className="flex flex-wrap items-center gap-3 px-5 py-3 text-sm">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-900 dark:text-white">{o.titulo}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {TIPOS_OPORTUNIDAD[o.tipo]} · {o.entidad || 'Sin entidad'} · cierra {formatDate(o.cierra_en)}{o.monto ? ` · ${formatCOP(o.monto)}` : ''}
                </p>
              </div>
              {o.url && <a href={o.url} target="_blank" rel="noreferrer" className="rounded p-1 text-slate-500 hover:text-slate-800" aria-label="Abrir enlace"><ExternalLink size={14} /></a>}
              <button className="rounded p-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-100" onClick={() => setEditando(o)} aria-label={`Editar ${o.titulo}`}><Pencil size={14} /></button>
              <button className="rounded p-1 text-slate-500 hover:text-rose-600" aria-label={`Eliminar ${o.titulo}`} onClick={async () => {
                if (!(await confirmar({ titulo: `¿Eliminar «${o.titulo}»?`, aceptar: 'Eliminar', peligro: true }))) return
                try { await eliminarOportunidad(o.id); void recargar() } catch (e) { setFallo((e as Error).message) }
              }}><Trash2 size={14} /></button>
            </li>
          ))}
        </ul>
      )}
      {editando && <FormOportunidad o={editando === 'nueva' ? null : editando} alCerrar={() => setEditando(null)} alGuardar={() => { setEditando(null); void recargar() }} />}
    </div>
  )
}

function FormOportunidad({ o, alCerrar, alGuardar }: { o: Oportunidad | null; alCerrar: () => void; alGuardar: () => void }) {
  const areas = useAreas()
  const ods = useOds()
  const [f, setF] = useState<OportunidadEntrada>({
    titulo: o?.titulo ?? '', entidad: o?.entidad ?? '', tipo: o?.tipo ?? 'convocatoria', descripcion: o?.descripcion ?? '',
    monto: o?.monto ?? null, cierra_en: o?.cierra_en ?? new Date().toISOString().slice(0, 10), url: o?.url ?? '',
    areas: o?.areas ?? [], ods: o?.ods ?? [],
  })
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const alternar = <T,>(xs: T[], x: T) => (xs.includes(x) ? xs.filter((y) => y !== x) : [...xs, x])

  return (
    <Modal titulo={o ? 'Editar oportunidad' : 'Nueva oportunidad'} alCerrar={alCerrar} ancho="max-w-2xl">
      <form className="space-y-3" onSubmit={async (e) => {
        e.preventDefault()
        setOcupado(true)
        try {
          if (o) await editarOportunidad(o.id, f)
          else await crearOportunidad(f)
          alGuardar()
        } catch (err) {
          setError((err as Error).message)
          setOcupado(false)
        }
      }}>
        <label className="block"><span className="label">Título</span>
          <input className="input" required minLength={5} maxLength={200} value={f.titulo} onChange={(e) => setF({ ...f, titulo: e.target.value })} /></label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block"><span className="label">Entidad</span>
            <input className="input" maxLength={150} value={f.entidad} onChange={(e) => setF({ ...f, entidad: e.target.value })} /></label>
          <label className="block"><span className="label">Tipo</span>
            <select className="input" value={f.tipo} onChange={(e) => setF({ ...f, tipo: e.target.value as Oportunidad['tipo'] })}>
              {Object.entries(TIPOS_OPORTUNIDAD).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select></label>
          <label className="block"><span className="label">Cierra</span>
            <input className="input" type="date" required value={f.cierra_en} onChange={(e) => setF({ ...f, cierra_en: e.target.value })} /></label>
          <label className="block"><span className="label">Monto (COP, opcional)</span>
            <input className="input tabular-nums" type="number" min={0} value={f.monto ?? ''} onChange={(e) => setF({ ...f, monto: e.target.value ? Number(e.target.value) : null })} /></label>
        </div>
        <label className="block"><span className="label">Enlace</span>
          <input className="input" type="url" maxLength={500} value={f.url} onChange={(e) => setF({ ...f, url: e.target.value })} placeholder="https://" /></label>
        <label className="block"><span className="label">Descripción</span>
          <textarea className="input min-h-20" value={f.descripcion} onChange={(e) => setF({ ...f, descripcion: e.target.value })} /></label>
        <fieldset><legend className="label">Áreas</legend>
          <div className="flex flex-wrap gap-1.5">
            {areas.map((a) => (
              <button type="button" key={a} onClick={() => setF({ ...f, areas: alternar(f.areas, a) })} aria-pressed={f.areas.includes(a)}
                className={`rounded-full px-2.5 py-1 text-xs ${f.areas.includes(a) ? 'bg-brand-600 text-white dark:bg-brand-300 dark:text-brand-950' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>{a}</button>
            ))}
          </div>
        </fieldset>
        <fieldset><legend className="label">ODS</legend>
          <div className="flex flex-wrap gap-1.5">
            {ods.map((x) => (
              <button type="button" key={x.id} title={x.nombre} onClick={() => setF({ ...f, ods: alternar(f.ods, x.id) })} aria-pressed={f.ods.includes(x.id)}
                className={`h-7 w-7 rounded-full text-xs tabular-nums ${f.ods.includes(x.id) ? 'bg-accent-600 text-white' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}`}>{x.id}</button>
            ))}
          </div>
        </fieldset>
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button><BotonGuardar ocupado={ocupado} /></div>
      </form>
    </Modal>
  )
}

function Actores() {
  const { datos, error, recargar } = useCarga(listarActores)
  const [editando, setEditando] = useState<Actor | 'nuevo' | null>(null)
  const [fallo, setFallo] = useState('')
  const { confirmar, ventana } = useConfirmar()
  return (
    <div className="space-y-3">
      {ventana}
      <button className="btn-primary" onClick={() => setEditando('nuevo')}><Plus size={15} aria-hidden /> Nuevo actor</button>
      <Aviso>{error || fallo}</Aviso>
      {!datos ? <Skeleton className="h-80" /> : (
        <ul className="card divide-y divide-slate-200 dark:divide-slate-800">
          {datos.length === 0 && <li className="px-5 py-10 text-center text-sm text-slate-500">Sin actores.</li>}
          {datos.map((a) => (
            <li key={a.id} className="flex flex-wrap items-center gap-3 px-5 py-3 text-sm">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-slate-900 dark:text-white">{a.nombre}</p>
                <p className="text-xs text-slate-500 capitalize dark:text-slate-400">{a.tipo} · {a.sector || 'Sin sector'} · {a.proyectos} proyectos</p>
              </div>
              <button className="rounded p-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-100" onClick={() => setEditando(a)} aria-label={`Editar ${a.nombre}`}><Pencil size={14} /></button>
              <button className="rounded p-1 text-slate-500 hover:text-rose-600" aria-label={`Eliminar ${a.nombre}`} onClick={async () => {
                if (!(await confirmar({ titulo: `¿Eliminar «${a.nombre}»?`, detalle: a.proyectos ? `Se quitará de ${a.proyectos} proyectos.` : undefined, aceptar: 'Eliminar', peligro: true }))) return
                try { await eliminarActor(a.id); void recargar() } catch (e) { setFallo((e as Error).message) }
              }}><Trash2 size={14} /></button>
            </li>
          ))}
        </ul>
      )}
      {editando && <FormActor a={editando === 'nuevo' ? null : editando} alCerrar={() => setEditando(null)} alGuardar={() => { setEditando(null); void recargar() }} />}
    </div>
  )
}

function FormActor({ a, alCerrar, alGuardar }: { a: Actor | null; alCerrar: () => void; alGuardar: () => void }) {
  const [f, setF] = useState<ActorEntrada>({ nombre: a?.nombre ?? '', tipo: a?.tipo ?? 'empresa', sector: a?.sector ?? '', contacto: a?.contacto ?? '' })
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  return (
    <Modal titulo={a ? 'Editar actor' : 'Nuevo actor'} alCerrar={alCerrar}>
      <form className="space-y-3" onSubmit={async (e) => {
        e.preventDefault()
        setOcupado(true)
        try {
          if (a) await editarActor(a.id, f)
          else await crearActor(f)
          alGuardar()
        } catch (err) {
          setError((err as Error).message)
          setOcupado(false)
        }
      }}>
        <label className="block"><span className="label">Nombre</span>
          <input className="input" required minLength={2} maxLength={200} value={f.nombre} onChange={(e) => setF({ ...f, nombre: e.target.value })} /></label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block"><span className="label">Tipo</span>
            <select className="input capitalize" value={f.tipo} onChange={(e) => setF({ ...f, tipo: e.target.value as TipoActor })}>
              {TIPOS_ACTOR.map((t) => <option key={t} value={t}>{t}</option>)}
            </select></label>
          <label className="block"><span className="label">Sector</span>
            <input className="input" maxLength={150} value={f.sector} onChange={(e) => setF({ ...f, sector: e.target.value })} /></label>
        </div>
        <label className="block"><span className="label">Contacto</span>
          <input className="input" maxLength={200} value={f.contacto} onChange={(e) => setF({ ...f, contacto: e.target.value })} /></label>
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button><BotonGuardar ocupado={ocupado} /></div>
      </form>
    </Modal>
  )
}

const FILTROS_POSTULACION: [EstadoPostulacion | '', string][] = [['enviada', 'Por decidir'], ['aceptada', 'Seleccionadas'], ['no_seleccionada', 'No seleccionadas'], ['', 'Todas']]

/** Proyectos postulados a las oportunidades: marcar como seleccionado o no seleccionado (con comentario). */
function Postulaciones() {
  const [estado, setEstado] = useState<EstadoPostulacion | ''>('enviada')
  const lista = useCarga(() => adminPostulaciones.listar({ estado: estado || undefined }), [estado])
  return (
    <section className="card">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <div>
          <h2 className="font-semibold text-slate-900 dark:text-white">Postulaciones</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">El equipo recibe la respuesta en la campana y por correo. Si queda seleccionado, todo el equipo gana experiencia.</p>
        </div>
        <div role="tablist" className="inline-flex rounded-lg bg-slate-100 p-0.5 dark:bg-slate-800">
          {FILTROS_POSTULACION.map(([v, texto]) => (
            <button key={texto} role="tab" aria-selected={estado === v} onClick={() => setEstado(v)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium ${estado === v ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-950 dark:text-white' : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}`}>
              {texto}
            </button>
          ))}
        </div>
      </header>
      <div className="p-5">
        <Aviso>{lista.error}</Aviso>
        {!lista.datos ? <Skeleton className="h-32" /> : lista.datos.length === 0 ? (
          <p className="py-6 text-center text-sm text-slate-500">{estado === 'enviada' ? 'No hay postulaciones por decidir.' : 'Sin postulaciones.'}</p>
        ) : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {lista.datos.map((p) => (
              <FilaPostulacion key={p.id} p={p} alDecidir={(nueva) =>
                lista.setDatos((xs) => (estado === 'enviada' ? xs?.filter((x) => x.id !== nueva.id) : xs?.map((x) => (x.id === nueva.id ? nueva : x))) ?? null)} />
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}

function FilaPostulacion({ p, alDecidir }: { p: Postulacion; alDecidir: (p: Postulacion) => void }) {
  const [comentario, setComentario] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')

  const decidir = async (estado: 'aceptada' | 'no_seleccionada') => {
    if (estado === 'no_seleccionada' && comentario.trim().length < 3) {
      setError('Escribe un comentario para el equipo (por qué no fue seleccionado).')
      return
    }
    setOcupado(true)
    setError('')
    try {
      alDecidir(await adminPostulaciones.decidir(p.id, estado, comentario.trim()))
    } catch (e) {
      setError((e as Error).message)
      setOcupado(false)
    }
  }

  return (
    <li className="py-4">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            <Link to={`/proyectos/${p.proyecto_id}`} className="hover:underline">{p.proyecto_titulo}</Link>
            <span className="font-normal text-slate-500"> → {p.oportunidad_titulo}</span>
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {p.oportunidad_entidad} · cierra el {formatDate(p.oportunidad_cierra_en)} · postulado el {formatDate(p.creado_en)}{p.usuario_nombre && ` por ${p.usuario_nombre}`}
          </p>
          <p className="mt-1 rounded-md bg-slate-50 px-2 py-1.5 text-sm text-slate-700 dark:bg-slate-900 dark:text-slate-300">{p.nota}</p>
          {p.comentario && <p className="mt-1 text-xs text-slate-500">Respuesta: «{p.comentario}»</p>}
        </div>
        <EstadoPostulacionBadge p={p} />
      </div>
      {p.estado === 'enviada' && (
        <div className="mt-3 flex flex-wrap items-end gap-2">
          <label className="block min-w-48 flex-1">
            <span className="label">Comentario para el equipo</span>
            <input className="input py-1.5" maxLength={1000} value={comentario} onChange={(e) => setComentario(e.target.value)}
              placeholder="Próximos pasos o motivo de la decisión" />
          </label>
          <button className="btn bg-emerald-600 py-1.5 text-white hover:bg-emerald-700" disabled={ocupado} onClick={() => decidir('aceptada')}>
            <Check size={15} aria-hidden /> Seleccionado
          </button>
          <button className="btn-ghost py-1.5 text-rose-700 dark:text-rose-400" disabled={ocupado} onClick={() => decidir('no_seleccionada')}>
            <X size={15} aria-hidden /> No seleccionado
          </button>
          {error && <p className="basis-full text-sm text-rose-600">{error}</p>}
        </div>
      )}
    </li>
  )
}
