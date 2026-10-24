import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Award, Minus, Pencil, Plus, RefreshCw, Search, Trash2, UserRound } from 'lucide-react'
import { adminXP, formatoXP, listarNiveles, olvidarNivel } from '@/lib/experiencia'
import { catalogoInsignias } from '@/lib/insignias'
import type { AccionXP, Insignia, Nivel, NivelEntrada, PersonaXP, ResumenUsuarioXP } from '@/lib/types'
import { Modal } from '@/components/Modal'
import { Skeleton } from '@/components/ui'
import { useConfirmar } from '@/components/Confirmar'
import { COLORES, ICONOS, NivelChip } from '@/components/Insignia'
import { MedallaNivel } from '@/components/Nivel'
import { hace } from '@/components/IconoAviso'
import { Aviso, BotonGuardar, Interruptor, Tarjeta, useCarga } from './comun'

/** Niveles, puntos por acción y ajustes manuales de experiencia. */
export function NivelesXP() {
  const niveles = useCarga(listarNiveles)
  const acciones = useCarga(adminXP.acciones)
  const insignias = useCarga(catalogoInsignias)
  const [editando, setEditando] = useState<Nivel | 'nuevo' | null>(null)
  const [aviso, setAviso] = useState('')
  const [error, setError] = useState('')
  const [recalculando, setRecalculando] = useState(false)
  const { confirmar, ventana } = useConfirmar()

  const eliminar = async (n: Nivel) => {
    if (!(await confirmar({
      titulo: `¿Eliminar el nivel «${n.nombre}»?`,
      detalle: n.personas ? `${n.personas} ${n.personas === 1 ? 'persona está' : 'personas están'} en este nivel y pasarán al que les corresponda.` : 'Nadie está en este nivel.',
      aceptar: 'Eliminar', peligro: true,
    }))) return
    try {
      await adminXP.eliminarNivel(n.id)
      olvidarNivel()
      niveles.recargar()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const recalcular = async () => {
    setRecalculando(true)
    setAviso('')
    try {
      const r = await adminXP.recalcular()
      olvidarNivel()
      niveles.recargar()
      setAviso(r.subieron ? `Listo. ${r.subieron} ${r.subieron === 1 ? 'persona subió' : 'personas subieron'} de nivel.` : 'Listo. Todos los niveles estaban al día.')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setRecalculando(false)
    }
  }

  return (
    <div className="space-y-6">
      {ventana}
      {editando && insignias.datos && (
        <FormNivel n={editando === 'nuevo' ? null : editando} insignias={insignias.datos} alCerrar={() => setEditando(null)}
          alGuardar={() => { setEditando(null); olvidarNivel(); niveles.recargar() }} />
      )}
      <Aviso>{error}</Aviso>
      <Aviso tipo="ok">{aviso}</Aviso>

      <Tarjeta titulo="Niveles"
        descripcion="Se suben en orden según la XP mínima. Cada nivel puede pedir además cierta cantidad de insignias vigentes o insignias específicas. Al editar, se actualiza el nivel de todos."
        extra={
          <div className="flex gap-2">
            <button className="btn-ghost text-sm" onClick={recalcular} disabled={recalculando} title="Vuelve a sumar la XP del historial y recalcula los niveles">
              <RefreshCw size={14} className={recalculando ? 'animate-spin' : ''} aria-hidden /> Recalcular
            </button>
            <button className="btn-primary text-sm" onClick={() => setEditando('nuevo')} disabled={!insignias.datos}>
              <Plus size={14} aria-hidden /> Nuevo nivel
            </button>
          </div>
        }>
        <Aviso>{niveles.error}</Aviso>
        {!niveles.datos ? <Skeleton className="h-48" /> : (
          <div className="-mx-5 overflow-x-auto">
            <table className="w-full min-w-[40rem] text-sm">
              <thead className="text-left text-xs text-slate-500">
                <tr className="border-b border-slate-200 dark:border-slate-800">
                  <th className="px-5 py-2 font-medium">Nivel</th>
                  <th className="px-3 py-2 text-right font-medium">XP mínima</th>
                  <th className="px-3 py-2 text-right font-medium">Insignias</th>
                  <th className="px-3 py-2 font-medium">Obligatorias</th>
                  <th className="px-3 py-2 text-right font-medium">Personas</th>
                  <th className="px-5 py-2" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {niveles.datos.map((n) => (
                  <tr key={n.id}>
                    <td className="px-5 py-2.5">
                      <div className="flex items-center gap-3">
                        <MedallaNivel nivel={n} tamano="md" />
                        <div className="min-w-0">
                          <p className="font-medium text-slate-900 dark:text-white">{n.nombre}</p>
                          <p className="max-w-xs truncate text-xs text-slate-500" title={n.descripcion}>{n.descripcion}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums">{n.xp_minima.toLocaleString('es-CO')}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums">{n.insignias_minimas || '—'}</td>
                    <td className="px-3 py-2.5 text-xs text-slate-600 dark:text-slate-300">
                      {n.insignias_requeridas.map((id) => insignias.datos?.find((i) => i.id === id)?.nombre ?? `#${id}`).join(', ') || '—'}
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums">{n.personas}</td>
                    <td className="px-5 py-2.5">
                      <div className="flex justify-end gap-1">
                        <button className="btn-ghost px-2 py-1" onClick={() => setEditando(n)} aria-label={`Editar ${n.nombre}`} disabled={!insignias.datos}>
                          <Pencil size={13} aria-hidden />
                        </button>
                        <button className="btn-ghost px-2 py-1 text-rose-700 dark:text-rose-400" onClick={() => eliminar(n)} aria-label={`Eliminar ${n.nombre}`}
                          disabled={niveles.datos!.length <= 1}>
                          <Trash2 size={13} aria-hidden />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Tarjeta>

      <Tarjeta titulo="Puntos por acción"
        descripcion="Cuánta experiencia da cada acción y cuántas veces al día puede sumar (vacío = sin tope). Una acción desactivada deja de sumar; lo ya ganado se conserva.">
        <Aviso>{acciones.error}</Aviso>
        {!acciones.datos ? <Skeleton className="h-64" /> : (
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {acciones.datos.map((a) => (
              <FilaAccion key={a.clave} a={a} alGuardar={(nueva) => acciones.setDatos((xs) => xs?.map((x) => (x.clave === nueva.clave ? nueva : x)) ?? null)} />
            ))}
          </ul>
        )}
      </Tarjeta>

      <AjusteManual />
    </div>
  )
}

function FilaAccion({ a, alGuardar }: { a: AccionXP; alGuardar: (a: AccionXP) => void }) {
  const [puntos, setPuntos] = useState(String(a.puntos))
  const [tope, setTope] = useState(a.tope_diario ? String(a.tope_diario) : '')
  const [estado, setEstado] = useState('')
  const cambio = puntos !== String(a.puntos) || tope !== (a.tope_diario ? String(a.tope_diario) : '')

  const guardar = async (activo = a.activo) => {
    setEstado('guardando')
    try {
      const nueva = await adminXP.editarAccion(a.clave, {
        nombre: a.nombre, descripcion: a.descripcion, puntos: Number(puntos) || 0, tope_diario: tope ? Number(tope) : null, activo,
      })
      alGuardar(nueva)
      setEstado('Guardado')
    } catch (e) {
      setEstado((e as Error).message)
    }
  }

  return (
    <li className={`flex flex-wrap items-center gap-3 py-2.5 ${a.activo ? '' : 'opacity-60'}`}>
      <Interruptor activo={a.activo} etiqueta={`${a.nombre} activa`} alCambiar={(v) => guardar(v)} disabled={estado === 'guardando'} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{a.nombre}</p>
        <p className="text-xs text-slate-500 dark:text-slate-400">{a.descripcion}</p>
      </div>
      <form className="flex items-center gap-2" onSubmit={(e) => { e.preventDefault(); guardar() }}>
        <label className="flex items-center gap-1.5 text-xs text-slate-500">
          <input type="number" min={0} max={100000} className="input w-20 py-1 text-right tabular-nums" value={puntos}
            onChange={(e) => setPuntos(e.target.value)} aria-label={`Puntos de ${a.nombre}`} /> XP
        </label>
        <label className="flex items-center gap-1.5 text-xs text-slate-500">
          tope
          <input type="number" min={1} max={1000} placeholder="—" className="input w-16 py-1 text-right tabular-nums" value={tope}
            onChange={(e) => setTope(e.target.value)} aria-label={`Tope diario de ${a.nombre}`} />
          /día
        </label>
        <button className="btn-ghost px-2.5 py-1 text-xs" disabled={!cambio || estado === 'guardando'}>Guardar</button>
      </form>
      {estado && estado !== 'guardando' && (
        <span className={`basis-full text-right text-xs ${estado === 'Guardado' ? 'text-emerald-600' : 'text-rose-600'}`}>{estado}</span>
      )}
    </li>
  )
}

function FormNivel({ n, insignias, alCerrar, alGuardar }: { n: Nivel | null; insignias: Insignia[]; alCerrar: () => void; alGuardar: () => void }) {
  const [f, setF] = useState<NivelEntrada>({
    nombre: n?.nombre ?? '', descripcion: n?.descripcion ?? '', icono: n?.icono ?? 'star', color: n?.color ?? 'brand',
    xp_minima: n?.xp_minima ?? 0, insignias_minimas: n?.insignias_minimas ?? 0, insignias_requeridas: n?.insignias_requeridas ?? [],
  })
  const [buscarIcono, setBuscarIcono] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const iconos = Object.keys(ICONOS).filter((k) => !buscarIcono.trim() || `${k} ${ICONOS[k][1]}`.toLowerCase().includes(buscarIcono.trim().toLowerCase()))
  const vista = { id: n?.id ?? 0, nombre: f.nombre || 'Nivel', icono: f.icono, color: f.color, posicion: n?.posicion ?? 0 }

  const alternarInsignia = (id: number) =>
    setF({ ...f, insignias_requeridas: f.insignias_requeridas.includes(id) ? f.insignias_requeridas.filter((x) => x !== id) : [...f.insignias_requeridas, id] })

  return (
    <Modal titulo={n ? `Editar «${n.nombre}»` : 'Nuevo nivel'} alCerrar={alCerrar} ancho="max-w-2xl">
      <form className="space-y-5" onSubmit={async (e) => {
        e.preventDefault()
        setOcupado(true)
        setError('')
        try {
          await (n ? adminXP.editarNivel(n.id, f) : adminXP.crearNivel(f))
          alGuardar()
        } catch (err) {
          setError((err as Error).message)
          setOcupado(false)
        }
      }}>
        <div className="flex items-start gap-4">
          <MedallaNivel nivel={vista} />
          <div className="flex-1 space-y-2">
            <input className="input" required minLength={2} maxLength={60} placeholder="Nombre (p. ej. «Explorador»)" aria-label="Nombre"
              value={f.nombre} onChange={(e) => setF({ ...f, nombre: e.target.value })} />
            <textarea className="input min-h-14" maxLength={500} placeholder="Qué significa llegar a este nivel" aria-label="Descripción"
              value={f.descripcion} onChange={(e) => setF({ ...f, descripcion: e.target.value })} />
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="label">Experiencia mínima (XP)</span>
            <input type="number" min={0} max={10000000} required className="input tabular-nums" value={f.xp_minima}
              onChange={(e) => setF({ ...f, xp_minima: Number(e.target.value) })} />
          </label>
          <label className="block">
            <span className="label">Insignias vigentes mínimas</span>
            <input type="number" min={0} max={1000} className="input tabular-nums" value={f.insignias_minimas}
              onChange={(e) => setF({ ...f, insignias_minimas: Number(e.target.value) })} />
          </label>
        </div>

        <fieldset>
          <legend className="label">Insignias obligatorias <span className="font-normal text-slate-400">(opcional)</span></legend>
          <div className="flex max-h-36 flex-wrap gap-1.5 overflow-y-auto">
            {insignias.map((i) => {
              const activa = f.insignias_requeridas.includes(i.id)
              return (
                <button type="button" key={i.id} onClick={() => alternarInsignia(i.id)} aria-pressed={activa}
                  className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs ${activa
                    ? 'border-brand-600 bg-brand-50 text-brand-800 dark:border-brand-300 dark:bg-brand-500/10 dark:text-brand-200'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800'}`}>
                  <Award size={11} aria-hidden /> {i.nombre}
                </button>
              )
            })}
          </div>
        </fieldset>

        <fieldset>
          <legend className="label">Ícono</legend>
          <div className="relative mb-2 max-w-xs">
            <Search size={14} className="absolute top-1/2 left-2.5 -translate-y-1/2 text-slate-400" aria-hidden />
            <input className="input py-1.5 pl-8" placeholder="Buscar: corona, cerebro, brújula…" value={buscarIcono} onChange={(e) => setBuscarIcono(e.target.value)} aria-label="Buscar ícono" />
          </div>
          <div className="grid max-h-36 grid-cols-[repeat(auto-fill,minmax(2.25rem,1fr))] gap-1.5 overflow-y-auto pr-1">
            {iconos.map((nombre) => {
              const Icono = ICONOS[nombre][0]
              return (
                <button type="button" key={nombre} onClick={() => setF({ ...f, icono: nombre })} aria-pressed={f.icono === nombre}
                  aria-label={ICONOS[nombre][1]} title={ICONOS[nombre][1]}
                  className={`grid h-9 w-9 place-items-center rounded-md border ${f.icono === nombre ? 'border-brand-600 bg-brand-50 text-brand-700 dark:border-brand-300 dark:bg-brand-500/10 dark:text-brand-200' : 'border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800'}`}>
                  <Icono size={16} aria-hidden />
                </button>
              )
            })}
          </div>
        </fieldset>

        <fieldset>
          <legend className="label">Color</legend>
          <div className="flex flex-wrap gap-2">
            {Object.keys(COLORES).map((c) => (
              <button type="button" key={c} onClick={() => setF({ ...f, color: c })} aria-pressed={f.color === c} aria-label={c} title={c}
                className={`h-8 w-8 rounded-full ring-1 ${COLORES[c]} ${f.color === c ? 'outline-2 outline-offset-2 outline-brand-600 dark:outline-brand-300' : ''}`} />
            ))}
          </div>
        </fieldset>

        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button><BotonGuardar ocupado={ocupado} /></div>
      </form>
    </Modal>
  )
}

/** Sumar o restar XP a una persona con un motivo, y ver su historial. Abre con ?persona=<id>. */
function AjusteManual() {
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState('')
  const [resultados, setResultados] = useState<PersonaXP[]>([])
  const [persona, setPersona] = useState<ResumenUsuarioXP | null>(null)
  const [signo, setSigno] = useState<1 | -1>(1)
  const [puntos, setPuntos] = useState('')
  const [motivo, setMotivo] = useState('')
  const [estado, setEstado] = useState('')
  const elegida = params.get('persona')

  useEffect(() => {
    if (!elegida) return
    adminXP.usuario(elegida).then((p) => {
      setPersona(p)
      document.getElementById('ajuste-xp')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }).catch((e: Error) => setEstado(e.message))
  }, [elegida])

  useEffect(() => {
    if (q.trim().length < 2) {
      setResultados([])
      return
    }
    const t = window.setTimeout(() => adminXP.personas(q.trim()).then(setResultados).catch(() => setResultados([])), 250)
    return () => window.clearTimeout(t)
  }, [q])

  const elegir = (id: string) => {
    setQ('')
    setResultados([])
    setEstado('')
    setParams((p) => {
      p.set('persona', id)
      return p
    }, { replace: true })
  }

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!persona) return
    setEstado('guardando')
    try {
      const valor = signo * Math.abs(Number(puntos))
      setPersona(await adminXP.ajustar(persona.usuario_id, valor, motivo.trim()))
      olvidarNivel(persona.usuario_id)
      setPuntos('')
      setMotivo('')
      setEstado(`Listo: ${valor > 0 ? '+' : ''}${valor} XP.`)
    } catch (err) {
      setEstado((err as Error).message)
    }
  }

  return (
    <div id="ajuste-xp" className="scroll-mt-24">
      <Tarjeta titulo="Ajustar experiencia" descripcion="Suma XP por algo que pasó fuera de la plataforma (un evento, una mentoría) o corrige un error. Queda en el historial de la persona con el motivo y en la bitácora.">
        <div className="relative max-w-md">
          <Search size={14} className="absolute top-1/2 left-2.5 -translate-y-1/2 text-slate-400" aria-hidden />
          <input className="input pl-8" placeholder="Buscar persona por nombre o correo" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Buscar persona" />
          {resultados.length > 0 && (
            <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
              {resultados.map((r) => (
                <li key={r.id}>
                  <button type="button" className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800" onClick={() => elegir(r.id)}>
                    <span className="min-w-0 flex-1">
                      <span className="block font-medium text-slate-900 dark:text-white">{r.nombre}</span>
                      <span className="block truncate text-xs text-slate-500">{r.email} · {r.rol_nombre}</span>
                    </span>
                    <NivelChip nivel={r.nivel} xp={r.xp} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {persona && (
          <div className="mt-5 grid gap-6 lg:grid-cols-2">
            <form onSubmit={enviar} className="space-y-3">
              <p className="flex flex-wrap items-center gap-2 text-sm">
                <UserRound size={15} className="text-slate-400" aria-hidden />
                <b className="text-slate-900 dark:text-white">{persona.nombre}</b>
                <NivelChip nivel={persona.nivel} xp={persona.xp} />
                <span className="text-slate-500 tabular-nums">{formatoXP(persona.xp)}</span>
              </p>
              <div className="flex items-center gap-2">
                <div className="inline-flex rounded-md border border-slate-200 p-0.5 dark:border-slate-700" role="radiogroup" aria-label="Sumar o restar">
                  {([[1, 'Sumar', Plus], [-1, 'Restar', Minus]] as const).map(([s, texto, Icono]) => (
                    <button type="button" key={s} role="radio" aria-checked={signo === s} onClick={() => setSigno(s)}
                      className={`inline-flex items-center gap-1 rounded px-2.5 py-1 text-sm ${signo === s
                        ? (s === 1 ? 'bg-emerald-600 text-white' : 'bg-rose-600 text-white') : 'text-slate-600 dark:text-slate-300'}`}>
                      <Icono size={13} aria-hidden /> {texto}
                    </button>
                  ))}
                </div>
                <input type="number" min={1} max={100000} required className="input w-28 tabular-nums" placeholder="Puntos" aria-label="Puntos"
                  value={puntos} onChange={(e) => setPuntos(e.target.value)} />
                <span className="text-sm text-slate-500">XP</span>
              </div>
              <label className="block">
                <span className="label">Motivo (la persona lo verá)</span>
                <textarea className="input min-h-16" required minLength={5} maxLength={500} value={motivo} onChange={(e) => setMotivo(e.target.value)}
                  placeholder="Ponente en el encuentro regional de semilleros" />
              </label>
              <div className="flex items-center gap-3">
                <BotonGuardar ocupado={estado === 'guardando'}>{signo === 1 ? 'Sumar experiencia' : 'Restar experiencia'}</BotonGuardar>
                {estado && estado !== 'guardando' && <span className={`text-sm ${estado.startsWith('Listo') ? 'text-emerald-600' : 'text-rose-600'}`}>{estado}</span>}
              </div>
            </form>

            <div>
              <p className="label">Historial</p>
              {persona.historial.length === 0 ? <p className="text-sm text-slate-500">Sin movimientos.</p> : (
                <ul className="max-h-72 divide-y divide-slate-100 overflow-y-auto pr-1 dark:divide-slate-800">
                  {persona.historial.map((m) => (
                    <li key={m.id} className="flex items-start gap-2 py-1.5 text-sm">
                      <span className={`w-12 shrink-0 text-right font-semibold tabular-nums ${m.puntos >= 0 ? 'text-emerald-700 dark:text-emerald-400' : 'text-rose-700 dark:text-rose-400'}`}>
                        {m.puntos >= 0 ? '+' : ''}{m.puntos}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-slate-800 dark:text-slate-200">{m.accion_nombre}</span>
                        {(m.detalle || m.otorgado_por) && (
                          <span className="block truncate text-xs text-slate-500" title={m.detalle}>{m.detalle}{m.otorgado_por && ` · ${m.otorgado_por}`}</span>
                        )}
                      </span>
                      <span className="shrink-0 text-xs text-slate-400">{hace(m.creado_en)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </Tarjeta>
    </div>
  )
}
