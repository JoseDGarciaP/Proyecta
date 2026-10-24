import { useEffect, useMemo, useState } from 'react'
import { Award, CalendarClock, Pencil, Plus, RefreshCw, Search, Trash2, Users, X } from 'lucide-react'
import {
  candidatos, crearInsignia, editarInsignia, eliminarInsignia, evaluarInsignias, listarInsigniasAdmin, otorgadas,
  otorgarInsignia, otorgarVarios, proyectosParaOtorgar, retirarInsignia, type DatosEntrega, type InsigniaEntrada,
} from '@/lib/admin'
import { olvidarInsignias, opcionesInsignia } from '@/lib/insignias'
import { useAreas, useOds, useRoles } from '@/lib/parametros'
import type { Condicion, CriterioInsignia, Insignia, OpcionesInsignia, Otorgada, TipoInsignia } from '@/lib/types'
import { Badge, Skeleton } from '@/components/ui'
import { Modal } from '@/components/Modal'
import { useConfirmar } from '@/components/Confirmar'
import { COLORES, ICONOS, Medalla, TIPO_CLASE, TIPO_LABEL } from '@/components/Insignia'
import { Aviso, BotonGuardar, Interruptor, fechaHora, useCarga } from './comun'

const fechaCorta = (iso: string) => new Date(`${iso}T12:00:00`).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })

function vigencia(i: Insignia) {
  const partes = []
  if (i.vence_en) partes.push(`vence el ${fechaCorta(i.vence_en)}`)
  if (i.vigencia_dias) partes.push(`dura ${i.vigencia_dias} días`)
  return partes.join(' · ')
}

/** Insignias: crear con reglas o como condecoración, otorgar (a una o varias personas), ver quién las tiene. */
export function Insignias() {
  const { datos, error, recargar } = useCarga(listarInsigniasAdmin)
  const opciones = useCarga(opcionesInsignia)
  const [editando, setEditando] = useState<Insignia | 'nueva' | null>(null)
  const [otorgando, setOtorgando] = useState<Insignia | null>(null)
  const [viendo, setViendo] = useState<Insignia | null>(null)
  const [filtro, setFiltro] = useState<TipoInsignia | 'todas'>('todas')
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)
  const { confirmar, ventana } = useConfirmar()

  const revisar = async () => {
    setMensaje(null)
    try {
      const { otorgadas: n } = await evaluarInsignias()
      olvidarInsignias()
      setMensaje({ tipo: 'ok', texto: n ? `Se otorgaron ${n} insignias automáticas a quienes ya cumplían.` : 'Nadie tenía insignias automáticas pendientes.' })
      void recargar()
    } catch (e) {
      setMensaje({ tipo: 'error', texto: (e as Error).message })
    }
  }

  const entrada = (i: Insignia): InsigniaEntrada => {
    const { id: _id, otorgadas: _o, automatica: _a, texto_regla: _t, ...resto } = i
    return resto
  }

  const alternar = async (i: Insignia, activo: boolean) => {
    try {
      await editarInsignia(i.id, { ...entrada(i), activo })
      void recargar()
    } catch (e) {
      setMensaje({ tipo: 'error', texto: (e as Error).message })
    }
  }

  const visibles = datos?.filter((i) => filtro === 'todas' || i.tipo === filtro)

  return (
    <div className="space-y-4">
      {ventana}
      <div className="flex flex-wrap items-center gap-2">
        <button className="btn-primary" onClick={() => setEditando('nueva')}><Plus size={15} aria-hidden /> Nueva insignia</button>
        <button className="btn-ghost" onClick={revisar} title="Entrega las automáticas a quienes ya cumplen sus requisitos">
          <RefreshCw size={15} aria-hidden /> Revisar logros ahora
        </button>
        <div className="ml-auto inline-flex rounded-md border border-slate-200 p-0.5 text-sm dark:border-slate-700" role="group" aria-label="Filtrar por tipo">
          {(['todas', 'logro', 'condecoracion', 'reconocimiento'] as const).map((t) => (
            <button key={t} onClick={() => setFiltro(t)} aria-pressed={filtro === t}
              className={`rounded px-2.5 py-1 ${filtro === t ? 'bg-brand-600 text-white dark:bg-brand-300 dark:text-brand-950' : 'text-slate-600 dark:text-slate-300'}`}>
              {t === 'todas' ? 'Todas' : TIPO_LABEL[t]}
            </button>
          ))}
        </div>
      </div>
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Las automáticas se entregan solas cuando alguien cumple sus requisitos (al registrar proyectos, aprobar colaboraciones, cambiar de rol…) y en una revisión cada hora.
      </p>
      {mensaje && <Aviso tipo={mensaje.tipo}>{mensaje.texto}</Aviso>}
      <Aviso>{error}</Aviso>
      {!visibles ? <Skeleton className="h-96" /> : (
        <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {visibles.map((i) => (
            <li key={i.id} className={`card flex flex-col p-4 ${i.activo ? '' : 'opacity-60'}`}>
              <div className="flex items-start gap-3">
                <Medalla icono={i.icono} color={i.color} tipo={i.tipo} tamano="lg" />
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-slate-900 dark:text-white">{i.nombre}</p>
                  <div className="mt-0.5 flex flex-wrap gap-1">
                    <Badge className={TIPO_CLASE[i.tipo]}>{TIPO_LABEL[i.tipo]}</Badge>
                    <Badge className={i.automatica ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'}>
                      {i.automatica ? 'Automática' : 'Manual'}
                    </Badge>
                  </div>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{i.descripcion}</p>
                  {i.entidad && <p className="text-xs text-slate-500 dark:text-slate-400">En nombre de {i.entidad}</p>}
                  {i.automatica && <p className="mt-1 text-[11px] text-slate-600 dark:text-slate-300">Requisitos: {i.texto_regla}</p>}
                  {vigencia(i) && <p className="mt-0.5 flex items-center gap-1 text-[11px] text-slate-500"><CalendarClock size={11} aria-hidden /> {vigencia(i)}</p>}
                </div>
                <Interruptor activo={i.activo} etiqueta={`${i.nombre} activa`} alCambiar={(v) => alternar(i, v)} />
              </div>
              <div className="mt-auto flex flex-wrap items-center gap-1 pt-3">
                <button className="btn-ghost px-2.5 py-1 text-xs" onClick={() => setViendo(i)} title="Quiénes la tienen"><Users size={13} aria-hidden /> {i.otorgadas}</button>
                <button className="btn-ghost px-2.5 py-1 text-xs" disabled={!i.activo} onClick={() => setOtorgando(i)}><Award size={13} aria-hidden /> Otorgar</button>
                <span className="ml-auto flex">
                  <button className="rounded p-1.5 text-slate-500 hover:text-slate-800 dark:hover:text-slate-100" onClick={() => setEditando(i)} aria-label={`Editar ${i.nombre}`}><Pencil size={14} /></button>
                  <button className="rounded p-1.5 text-slate-500 hover:text-rose-600" aria-label={`Eliminar ${i.nombre}`} onClick={async () => {
                    if (!(await confirmar({ titulo: `¿Eliminar «${i.nombre}»?`, detalle: i.otorgadas ? `${i.otorgadas} personas la perderán. Si solo quieres dejar de entregarla, desactívala.` : undefined, aceptar: 'Eliminar', peligro: true }))) return
                    try { await eliminarInsignia(i.id); olvidarInsignias(); void recargar() } catch (e) { setMensaje({ tipo: 'error', texto: (e as Error).message }) }
                  }}><Trash2 size={14} /></button>
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
      {editando && opciones.datos && (
        <FormInsignia i={editando === 'nueva' ? null : editando} opciones={opciones.datos} alCerrar={() => setEditando(null)}
          alGuardar={(i) => {
            setEditando(null)
            olvidarInsignias()
            setMensaje({ tipo: 'ok', texto: i.automatica && i.otorgadas ? `«${i.nombre}» guardada: ${i.otorgadas} personas ya cumplen los requisitos y la recibieron.` : `«${i.nombre}» guardada.` })
            void recargar()
          }} />
      )}
      {otorgando && <OtorgarInsignia insignia={otorgando} alCerrar={() => setOtorgando(null)}
        alOtorgar={(texto) => { setOtorgando(null); setMensaje({ tipo: 'ok', texto }); void recargar() }} />}
      {viendo && <QuienesLaTienen insignia={viendo} alCerrar={() => { setViendo(null); void recargar() }} />}
    </div>
  )
}

// ---- Crear o editar ------------------------------------------------------------------------

const TIPOS_AYUDA: Record<TipoInsignia, string> = {
  logro: 'Por méritos medibles en la plataforma. Normalmente automática.',
  condecoracion: 'Distinción formal, p. ej. de una facultad o en un evento. Se ve con aro dorado.',
  reconocimiento: 'Agradecimiento o mención por un aporte. Se ve con aro punteado.',
}

function FormInsignia({ i, opciones, alCerrar, alGuardar }: { i: Insignia | null; opciones: OpcionesInsignia; alCerrar: () => void; alGuardar: (i: Insignia) => void }) {
  const [f, setF] = useState<InsigniaEntrada>({
    nombre: i?.nombre ?? '', descripcion: i?.descripcion ?? '', tipo: i?.tipo ?? 'logro', entidad: i?.entidad ?? '',
    icono: i?.icono ?? 'award', color: i?.color ?? 'amber', reglas: i?.reglas ?? null,
    vence_en: i?.vence_en ?? null, vigencia_dias: i?.vigencia_dias ?? null, activo: i?.activo ?? true, orden: i?.orden ?? 0,
  })
  const [buscarIcono, setBuscarIcono] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const iconos = opciones.iconos.filter((k) => !buscarIcono.trim() || `${k} ${ICONOS[k]?.[1] ?? ''}`.toLowerCase().includes(buscarIcono.trim().toLowerCase()))
  const automatica = Boolean(f.reglas)

  const setTipo = (tipo: TipoInsignia) =>
    setF({ ...f, tipo, reglas: tipo === 'logro' ? f.reglas : f.reglas })

  return (
    <Modal titulo={i ? `Editar «${i.nombre}»` : 'Nueva insignia'} alCerrar={alCerrar} ancho="max-w-2xl">
      <form className="space-y-5" onSubmit={async (e) => {
        e.preventDefault()
        setOcupado(true)
        setError('')
        try {
          alGuardar(i ? await editarInsignia(i.id, f) : await crearInsignia(f))
        } catch (err) {
          setError((err as Error).message)
          setOcupado(false)
        }
      }}>
        <fieldset>
          <legend className="label">¿Qué es?</legend>
          <div className="grid gap-2 sm:grid-cols-3">
            {(Object.keys(TIPO_LABEL) as TipoInsignia[]).map((t) => (
              <button type="button" key={t} onClick={() => setTipo(t)} aria-pressed={f.tipo === t}
                className={`rounded-lg border p-2.5 text-left ${f.tipo === t ? 'border-brand-600 bg-brand-50 dark:border-brand-300 dark:bg-brand-500/10' : 'border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'}`}>
                <span className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                  <Medalla icono={f.icono} color={f.color} tipo={t} tamano="sm" /> {TIPO_LABEL[t]}
                </span>
                <span className="mt-1 block text-[11px] leading-snug text-slate-500 dark:text-slate-400">{TIPOS_AYUDA[t]}</span>
              </button>
            ))}
          </div>
        </fieldset>

        <div className="flex items-start gap-4">
          <Medalla icono={f.icono} color={f.color} tipo={f.tipo} tamano="lg" />
          <div className="flex-1 space-y-2">
            <input className="input" required minLength={3} maxLength={80} placeholder="Nombre (p. ej. «Destacado del semestre»)" aria-label="Nombre"
              value={f.nombre} onChange={(e) => setF({ ...f, nombre: e.target.value })} />
            <textarea className="input min-h-14" maxLength={500} placeholder="Qué significa esta insignia" aria-label="Significado"
              value={f.descripcion} onChange={(e) => setF({ ...f, descripcion: e.target.value })} />
            {f.tipo !== 'logro' && (
              <input className="input" maxLength={150} placeholder="Otorgada en nombre de (opcional): Facultad de Ingenierías, Rectoría…" aria-label="En nombre de"
                value={f.entidad} onChange={(e) => setF({ ...f, entidad: e.target.value })} />
            )}
          </div>
        </div>

        <fieldset>
          <legend className="label flex w-full items-center justify-between gap-2">
            Ícono <span className="font-normal text-slate-400">{opciones.iconos.length} disponibles</span>
          </legend>
          <div className="relative mb-2 max-w-xs">
            <Search size={14} className="absolute top-1/2 left-2.5 -translate-y-1/2 text-slate-400" aria-hidden />
            <input className="input py-1.5 pl-8" placeholder="Buscar: libro, agua, código, trofeo…" value={buscarIcono} onChange={(e) => setBuscarIcono(e.target.value)} aria-label="Buscar ícono" />
          </div>
          <div className="grid max-h-44 grid-cols-[repeat(auto-fill,minmax(2.25rem,1fr))] gap-1.5 overflow-y-auto pr-1">
            {iconos.map((nombre) => {
              const Icono = ICONOS[nombre]?.[0] ?? Award
              return (
                <button type="button" key={nombre} onClick={() => setF({ ...f, icono: nombre })} aria-pressed={f.icono === nombre}
                  aria-label={ICONOS[nombre]?.[1] ?? nombre} title={ICONOS[nombre]?.[1] ?? nombre}
                  className={`grid h-9 w-9 place-items-center rounded-md border ${f.icono === nombre ? 'border-brand-600 bg-brand-50 text-brand-700 dark:border-brand-300 dark:bg-brand-500/10 dark:text-brand-200' : 'border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'}`}>
                  <Icono size={16} aria-hidden />
                </button>
              )
            })}
            {iconos.length === 0 && <p className="col-span-full text-xs text-slate-500">Sin resultados.</p>}
          </div>
        </fieldset>

        <fieldset>
          <legend className="label">Color</legend>
          <div className="flex flex-wrap gap-2">
            {opciones.colores.map((c) => (
              <button type="button" key={c} onClick={() => setF({ ...f, color: c })} aria-pressed={f.color === c} aria-label={c} title={c}
                className={`h-8 w-8 rounded-full ring-1 ${COLORES[c]} ${f.color === c ? 'outline-2 outline-offset-2 outline-brand-600 dark:outline-brand-300' : ''}`} />
            ))}
          </div>
        </fieldset>

        <fieldset className="space-y-3">
          <legend className="label">¿Cómo se obtiene?</legend>
          <div className="inline-flex rounded-md border border-slate-200 p-0.5 text-sm dark:border-slate-700">
            {[['manual', 'La otorga la administración'], ['auto', 'Automática por requisitos']].map(([v, l]) => {
              const activo = (v === 'auto') === automatica
              return (
                <button type="button" key={v} aria-pressed={activo}
                  onClick={() => setF({ ...f, reglas: v === 'auto' ? (f.reglas ?? { modo: 'todas', condiciones: [{ criterio: opciones.criterios[0].clave, umbral: 1, valor: null }] }) : null })}
                  className={`rounded px-3 py-1.5 ${activo ? 'bg-brand-600 text-white dark:bg-brand-300 dark:text-brand-950' : 'text-slate-600 dark:text-slate-300'}`}>{l}</button>
              )
            })}
          </div>
          {f.reglas ? (
            <EditorReglas reglas={f.reglas} criterios={opciones.criterios} alCambiar={(reglas) => setF({ ...f, reglas })} />
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-400">Se entrega a mano desde «Otorgar», a una persona, a varias o a todo el equipo de un proyecto, escribiendo el motivo.</p>
          )}
        </fieldset>

        <fieldset className="space-y-2">
          <legend className="label">Vigencia <span className="font-normal text-slate-400">(opcional)</span></legend>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
            <label className="flex items-center gap-2">
              <span className="text-slate-600 dark:text-slate-300">Vence el</span>
              <input type="date" className="input w-auto py-1.5" value={f.vence_en ?? ''} onChange={(e) => setF({ ...f, vence_en: e.target.value || null })} />
            </label>
            <label className="flex items-center gap-2">
              <span className="text-slate-600 dark:text-slate-300">o dura</span>
              <input type="number" min={1} max={3650} className="input w-24 py-1.5 tabular-nums" value={f.vigencia_dias ?? ''}
                onChange={(e) => setF({ ...f, vigencia_dias: e.target.value ? Number(e.target.value) : null })} />
              <span className="text-slate-600 dark:text-slate-300">días desde que se otorga</span>
            </label>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Útil para «Destacado del semestre 2026-2». Al vencer deja de mostrarse y queda en el historial de la persona.</p>
        </fieldset>

        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button><BotonGuardar ocupado={ocupado} /></div>
      </form>
    </Modal>
  )
}

/** Lista de requisitos: cada uno es un criterio con su meta (y un valor si lo necesita). */
function EditorReglas({ reglas, criterios, alCambiar }: {
  reglas: NonNullable<InsigniaEntrada['reglas']>; criterios: CriterioInsignia[]; alCambiar: (r: NonNullable<InsigniaEntrada['reglas']>) => void
}) {
  const areas = useAreas()
  const ods = useOds()
  const roles = useRoles()
  const grupos = useMemo(() => {
    const g = new Map<string, CriterioInsignia[]>()
    criterios.forEach((c) => g.set(c.grupo, [...(g.get(c.grupo) ?? []), c]))
    return [...g.entries()]
  }, [criterios])
  const porClave = Object.fromEntries(criterios.map((c) => [c.clave, c]))

  const cambiar = (k: number, c: Partial<Condicion>) =>
    alCambiar({ ...reglas, condiciones: reglas.condiciones.map((x, i) => (i === k ? { ...x, ...c } : x)) })

  return (
    <div className="space-y-2 rounded-lg border border-slate-200 p-3 dark:border-slate-800">
      {reglas.condiciones.length > 1 && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-600 dark:text-slate-300">Se otorga cuando cumple</span>
          <select className="input w-auto py-1" value={reglas.modo} onChange={(e) => alCambiar({ ...reglas, modo: e.target.value as 'todas' | 'alguna' })} aria-label="Modo">
            <option value="todas">todos los requisitos</option>
            <option value="alguna">al menos uno</option>
          </select>
        </div>
      )}
      <ol className="space-y-2">
        {reglas.condiciones.map((c, k) => {
          const def = porClave[c.criterio]
          return (
            <li key={k} className="flex flex-wrap items-center gap-2 text-sm">
              <span className="w-6 text-right text-xs text-slate-400">{k === 0 ? '' : reglas.modo === 'todas' ? 'y' : 'o'}</span>
              <select className="input w-auto max-w-full py-1.5" value={c.criterio} aria-label={`Requisito ${k + 1}`}
                onChange={(e) => cambiar(k, { criterio: e.target.value, valor: null, umbral: 1 })}>
                {grupos.map(([g, lista]) => (
                  <optgroup key={g} label={g}>
                    {lista.map((x) => <option key={x.clave} value={x.clave}>{x.nombre}</option>)}
                  </optgroup>
                ))}
              </select>
              {def?.valor === 'area' && (
                <select className="input w-auto py-1.5" required value={c.valor ?? ''} onChange={(e) => cambiar(k, { valor: e.target.value || null })} aria-label="Área">
                  <option value="">Elige el área</option>
                  {areas.map((a) => <option key={a} value={a}>{a}</option>)}
                </select>
              )}
              {def?.valor === 'ods' && (
                <select className="input w-auto max-w-60 py-1.5" required value={c.valor ?? ''} onChange={(e) => cambiar(k, { valor: e.target.value || null })} aria-label="ODS">
                  <option value="">Elige el ODS</option>
                  {ods.map((o) => <option key={o.id} value={String(o.id)}>{o.id}. {o.nombre}</option>)}
                </select>
              )}
              {def?.valor === 'rol' && (
                <select className="input w-auto py-1.5" required value={c.valor ?? ''} onChange={(e) => cambiar(k, { valor: e.target.value || null })} aria-label="Rol">
                  <option value="">Elige el rol</option>
                  {roles.map((r) => <option key={r.clave} value={r.clave}>{r.nombre}</option>)}
                </select>
              )}
              {def?.valor === 'texto' && (
                <input className="input w-48 py-1.5" required placeholder="p. ej. Sistemas" value={c.valor ?? ''} onChange={(e) => cambiar(k, { valor: e.target.value })} aria-label="Texto" />
              )}
              {!def?.binario && (
                <>
                  <span className="text-slate-500">mínimo</span>
                  <input type="number" min={1} max={100000} className="input w-20 py-1.5 tabular-nums" value={c.umbral}
                    onChange={(e) => cambiar(k, { umbral: Math.max(1, Number(e.target.value)) })} aria-label="Mínimo" />
                  <span className="text-slate-500">{def?.unidad}</span>
                </>
              )}
              {reglas.condiciones.length > 1 && (
                <button type="button" className="rounded p-1 text-slate-400 hover:text-rose-600" aria-label="Quitar requisito"
                  onClick={() => alCambiar({ ...reglas, condiciones: reglas.condiciones.filter((_, i) => i !== k) })}><X size={14} /></button>
              )}
            </li>
          )
        })}
      </ol>
      {reglas.condiciones.length < 8 && (
        <button type="button" className="text-xs font-medium text-brand-700 hover:underline dark:text-brand-300"
          onClick={() => alCambiar({ ...reglas, condiciones: [...reglas.condiciones, { criterio: criterios[0].clave, umbral: 1, valor: null }] })}>
          + Agregar requisito
        </button>
      )}
      <p className="text-xs text-slate-500">Al guardar, quienes ya cumplan los requisitos la reciben de una vez (con aviso).</p>
    </div>
  )
}

// ---- Otorgar ---------------------------------------------------------------------------------

type Persona = { id: string; nombre: string; detalle?: string }

/** Otorgar: desde una insignia (a una o varias personas, o a todo un equipo) o desde una persona (elige la insignia). */
export function OtorgarInsignia({ insignia, persona, alCerrar, alOtorgar }: {
  insignia?: Insignia; persona?: Persona; alCerrar: () => void; alOtorgar: (texto: string) => void
}) {
  const [elegida, setElegida] = useState<Insignia | null>(insignia ?? null)
  const [personas, setPersonas] = useState<Persona[]>(persona ? [persona] : [])
  const [proyecto, setProyecto] = useState<{ id: string; titulo: string; equipo: number } | null>(null)
  const [q, setQ] = useState('')
  const [qProyecto, setQProyecto] = useState('')
  const [resultados, setResultados] = useState<Persona[]>([])
  const [proyectos, setProyectos] = useState<{ id: string; titulo: string; equipo: number }[]>([])
  const [d, setD] = useState<DatosEntrega>({ motivo: '', fecha_evento: null, vence_en: null })
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const catalogo = useCarga(listarInsigniasAdmin)

  useEffect(() => {
    if (persona || q.trim().length < 2) return setResultados([])
    const t = window.setTimeout(() => candidatos(q.trim())
      .then((rs) => setResultados(rs.map((r) => ({ id: r.id, nombre: r.nombre, detalle: `${r.email} · ${r.rol_nombre}` }))))
      .catch(() => setResultados([])), 250)
    return () => window.clearTimeout(t)
  }, [q, persona])

  useEffect(() => {
    if (persona) return
    const t = window.setTimeout(() => proyectosParaOtorgar(qProyecto.trim()).then(setProyectos).catch(() => setProyectos([])), 250)
    return () => window.clearTimeout(t)
  }, [qProyecto, persona])

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!elegida) return setError('Elige la insignia.')
    if (!personas.length && !proyecto) return setError('Elige al menos una persona o un proyecto.')
    setOcupado(true)
    setError('')
    try {
      const datos = { ...d, motivo: d.motivo.trim() }
      if (personas.length === 1 && !proyecto) {
        await otorgarInsignia(elegida.id, personas[0].id, datos)
        olvidarInsignias(personas[0].id)
        alOtorgar(`«${elegida.nombre}» otorgada a ${personas[0].nombre}. Le avisamos en la plataforma y por correo.`)
      } else {
        const r = await otorgarVarios(elegida.id, personas.map((p) => p.id), proyecto?.id ?? null, datos)
        olvidarInsignias()
        alOtorgar(`«${elegida.nombre}» otorgada a ${r.otorgadas.length} ${r.otorgadas.length === 1 ? 'persona' : 'personas'}`
          + (r.otorgadas.length ? ` (${r.otorgadas.join(', ')})` : '') + (r.ya_tenian.length ? `. Ya la tenían: ${r.ya_tenian.join(', ')}.` : '.'))
      }
    } catch (err) {
      setError((err as Error).message)
      setOcupado(false)
    }
  }

  return (
    <Modal titulo={insignia ? `Otorgar «${insignia.nombre}»` : `Otorgar insignia a ${persona?.nombre}`}
      descripcion={insignia?.entidad ? `En nombre de ${insignia.entidad}` : undefined} alCerrar={alCerrar} ancho="max-w-xl">
      <form className="space-y-4" onSubmit={enviar}>
        {!insignia && (
          <fieldset>
            <legend className="label">Insignia</legend>
            {!catalogo.datos ? <Skeleton className="h-24" /> : (
              <div className="grid max-h-60 gap-1.5 overflow-y-auto sm:grid-cols-2">
                {catalogo.datos.filter((i) => i.activo).map((i) => (
                  <button type="button" key={i.id} onClick={() => setElegida(i)} aria-pressed={elegida?.id === i.id}
                    className={`flex items-center gap-2 rounded-md border px-2 py-1.5 text-left text-sm ${elegida?.id === i.id ? 'border-brand-600 bg-brand-50 dark:border-brand-300 dark:bg-brand-500/10' : 'border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'}`}>
                    <Medalla icono={i.icono} color={i.color} tipo={i.tipo} tamano="sm" /> <span className="truncate">{i.nombre}</span>
                    <span className="ml-auto text-[10px] text-slate-400">{TIPO_LABEL[i.tipo]}</span>
                  </button>
                ))}
              </div>
            )}
          </fieldset>
        )}

        {!persona && (
          <>
            <div>
              <label className="label" htmlFor="otorgar-buscar">Personas</label>
              {personas.length > 0 && (
                <ul className="mb-2 flex flex-wrap gap-1.5">
                  {personas.map((p) => (
                    <li key={p.id} className="inline-flex items-center gap-1 rounded-full bg-slate-100 py-1 pr-1 pl-3 text-xs dark:bg-slate-800">
                      {p.nombre}
                      <button type="button" className="rounded-full p-0.5 hover:bg-slate-200 dark:hover:bg-slate-700" aria-label={`Quitar a ${p.nombre}`}
                        onClick={() => setPersonas((xs) => xs.filter((x) => x.id !== p.id))}><X size={12} /></button>
                    </li>
                  ))}
                </ul>
              )}
              <div className="relative">
                <Search size={15} className="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" aria-hidden />
                <input id="otorgar-buscar" className="input pl-9" placeholder="Buscar por nombre o correo para agregar" value={q} onChange={(e) => setQ(e.target.value)} />
              </div>
              {resultados.length > 0 && (
                <ul className="mt-1 max-h-44 overflow-y-auto rounded-md border border-slate-200 dark:border-slate-700">
                  {resultados.filter((r) => !personas.some((p) => p.id === r.id)).map((r) => (
                    <li key={r.id}>
                      <button type="button" className="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800"
                        onClick={() => { setPersonas((xs) => [...xs, r]); setQ('') }}>
                        {r.nombre} <span className="text-xs text-slate-500">· {r.detalle}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <label className="label" htmlFor="otorgar-proyecto">…o todo el equipo de un proyecto <span className="font-normal text-slate-400">(responsable y miembros)</span></label>
              {proyecto ? (
                <p className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm dark:border-slate-700">
                  <span>{proyecto.titulo} <span className="text-xs text-slate-500">· {proyecto.equipo} personas</span></span>
                  <button type="button" className="text-xs text-brand-700 hover:underline dark:text-brand-300" onClick={() => setProyecto(null)}>Quitar</button>
                </p>
              ) : (
                <>
                  <input id="otorgar-proyecto" className="input" placeholder="Buscar proyecto" value={qProyecto} onChange={(e) => setQProyecto(e.target.value)} />
                  {qProyecto.trim() && proyectos.length > 0 && (
                    <ul className="mt-1 max-h-40 overflow-y-auto rounded-md border border-slate-200 dark:border-slate-700">
                      {proyectos.map((p) => (
                        <li key={p.id}>
                          <button type="button" className="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800" onClick={() => { setProyecto(p); setQProyecto('') }}>
                            {p.titulo} <span className="text-xs text-slate-500">· {p.equipo} personas</span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </>
              )}
            </div>
          </>
        )}

        <label className="block"><span className="label">Motivo <span className="font-normal text-slate-400">(lo verá la persona)</span></span>
          <textarea className="input min-h-20" required minLength={5} maxLength={500} value={d.motivo} onChange={(e) => setD({ ...d, motivo: e.target.value })}
            placeholder="Ej.: Primer lugar en la feria de proyectos 2026." /></label>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block"><span className="label">Fecha del evento <span className="font-normal text-slate-400">(opcional)</span></span>
            <input type="date" className="input" value={d.fecha_evento ?? ''} onChange={(e) => setD({ ...d, fecha_evento: e.target.value || null })} /></label>
          <label className="block"><span className="label">Vence el <span className="font-normal text-slate-400">(opcional)</span></span>
            <input type="date" className="input" value={d.vence_en ?? ''} onChange={(e) => setD({ ...d, vence_en: e.target.value || null })} />
            {elegida && vigencia(elegida) && !d.vence_en && <span className="mt-1 block text-[11px] text-slate-500">Si lo dejas vacío: {vigencia(elegida)}.</span>}
          </label>
        </div>
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button>
          <BotonGuardar ocupado={ocupado}>{personas.length + (proyecto ? proyecto.equipo : 0) > 1 ? 'Otorgar a todos' : 'Otorgar'}</BotonGuardar>
        </div>
      </form>
    </Modal>
  )
}

// ---- Quiénes la tienen -----------------------------------------------------------------------

const ESTADO_CLASE: Record<Otorgada['estado'], string> = {
  vigente: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  vencida: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  retirada: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
}

function QuienesLaTienen({ insignia, alCerrar }: { insignia: Insignia; alCerrar: () => void }) {
  const { datos, error, recargar } = useCarga(() => otorgadas(insignia.id), [insignia.id])
  const { confirmar, ventana } = useConfirmar()
  const [fallo, setFallo] = useState('')
  return (
    <Modal titulo={`Quiénes tienen «${insignia.nombre}»`} alCerrar={alCerrar} ancho="max-w-2xl">
      {ventana}
      <Aviso>{error || fallo}</Aviso>
      {!datos ? <Skeleton className="h-40" /> : datos.length === 0 ? <p className="text-sm text-slate-500">Nadie la tiene todavía.</p> : (
        <ul className="max-h-[60vh] divide-y divide-slate-200 overflow-y-auto dark:divide-slate-800">
          {datos.map((o) => (
            <li key={o.usuario_id} className={`flex items-start gap-3 py-2.5 text-sm ${o.estado !== 'vigente' ? 'opacity-60' : ''}`}>
              <div className="min-w-0 flex-1">
                <p className="flex flex-wrap items-center gap-1.5 font-medium text-slate-900 dark:text-white">
                  {o.nombre} <span className="font-normal text-slate-500">· {o.email}</span>
                  <Badge className={ESTADO_CLASE[o.estado]}>{o.estado}</Badge>
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {o.automatica ? 'Automática' : `Otorgada por ${o.otorgada_por ?? 'un admin'}`} · {fechaHora.format(new Date(o.otorgada_en))}
                  {o.fecha_evento && ` · evento ${fechaCorta(o.fecha_evento)}`}
                  {o.vence_en && ` · ${o.estado === 'vencida' ? 'venció' : 'vence'} ${fechaHora.format(new Date(o.vence_en))}`}
                  {o.retirada_en && ` · retirada ${fechaHora.format(new Date(o.retirada_en))}`}
                </p>
                {o.motivo && !o.automatica && <p className="text-xs text-slate-600 dark:text-slate-300">«{o.motivo}»</p>}
              </div>
              {o.estado === 'vigente' && (
                <button className="btn-ghost px-2 py-1 text-xs text-rose-700 dark:text-rose-400" onClick={async () => {
                  if (!(await confirmar({ titulo: `¿Retirar «${insignia.nombre}» a ${o.nombre}?`, detalle: o.automatica ? 'No se le volverá a dar sola; podrás otorgarla de nuevo a mano.' : undefined, aceptar: 'Retirar', peligro: true }))) return
                  try { await retirarInsignia(insignia.id, o.usuario_id); olvidarInsignias(o.usuario_id); void recargar() } catch (e) { setFallo((e as Error).message) }
                }}>Retirar</button>
              )}
            </li>
          ))}
        </ul>
      )}
    </Modal>
  )
}
