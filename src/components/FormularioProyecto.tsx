import { useState, type ReactNode } from 'react'
import { Loader2, Save } from 'lucide-react'
import { AREAS, ESTADOS, ESTADO_LABEL, type Area, type Estado, type NuevoProyecto, type Proyecto } from '@/lib/types'
import { useAreas, useOds } from '@/lib/parametros'
import { useSesion } from '@/lib/sesion'

/** Lo que se edita en el formulario (equipo y etiquetas como texto separado por comas). */
export interface DatosFormularioProyecto {
  titulo: string
  resumen: string
  descripcion: string
  necesidades: string
  area: Area
  estado: Estado
  avance: number
  presupuesto: number
  lider: string
  equipo: string
  etiquetas: string
  fecha_inicio: string
  fecha_fin: string
  ods: number[]
}

export const formularioVacio = (): DatosFormularioProyecto => ({
  titulo: '',
  resumen: '',
  descripcion: '',
  necesidades: '',
  area: AREAS[0] as Area,
  estado: 'idea',
  avance: 0,
  presupuesto: 0,
  lider: '',
  equipo: '',
  etiquetas: '',
  fecha_inicio: new Date().toISOString().slice(0, 10),
  fecha_fin: '',
  ods: [],
})

/** Carga un proyecto existente en el formulario (para editarlo). */
export const formularioDe = (p: Proyecto): DatosFormularioProyecto => ({
  titulo: p.titulo,
  resumen: p.resumen,
  descripcion: p.descripcion ?? '',
  necesidades: p.necesidades ?? '',
  area: p.area,
  estado: p.estado,
  avance: p.avance,
  presupuesto: p.presupuesto,
  lider: p.lider,
  equipo: p.equipo.join(', '),
  etiquetas: p.etiquetas.join(', '),
  fecha_inicio: p.fecha_inicio.slice(0, 10),
  fecha_fin: p.fecha_fin?.slice(0, 10) ?? '',
  ods: p.ods ?? [],
})

const separar = (valor: string) => [...new Set(valor.split(',').map((v) => v.trim()).filter(Boolean))]

/** Convierte el formulario en lo que recibe la API (sin actores: esos se gestionan aparte). */
export const datosDe = (f: DatosFormularioProyecto): Omit<NuevoProyecto, 'actores'> => ({
  titulo: f.titulo.trim(),
  resumen: f.resumen.trim(),
  descripcion: f.descripcion.trim(),
  necesidades: f.necesidades.trim(),
  area: f.area,
  estado: f.estado,
  avance: Number(f.avance),
  presupuesto: Number(f.presupuesto),
  lider: f.lider.trim(),
  equipo: separar(f.equipo),
  etiquetas: separar(f.etiquetas),
  fecha_inicio: f.fecha_inicio,
  fecha_fin: f.fecha_fin || null,
  ods: f.ods,
})

/** Formulario de los datos de un proyecto: lo usan «Registrar proyecto» y «Editar proyecto». */
export function FormularioProyecto({
  inicial, titulo, descripcion, textoBoton, alGuardar, acciones,
}: {
  inicial: DatosFormularioProyecto
  titulo: string
  descripcion: ReactNode
  textoBoton: string
  alGuardar: (datos: DatosFormularioProyecto) => Promise<void>
  /** Botones extra junto a «Guardar» (Limpiar, Cancelar…). Reciben cómo volver al estado inicial. */
  acciones?: (reiniciar: () => void) => ReactNode
}) {
  const [form, setForm] = useState(inicial)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { usuario } = useSesion()
  const areas = useAreas()
  const ods = useOds()

  const set = <K extends keyof DatosFormularioProyecto>(clave: K, valor: DatosFormularioProyecto[K]) =>
    setForm((f) => ({ ...f, [clave]: valor }))

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    if (form.fecha_fin && form.fecha_fin < form.fecha_inicio) {
      setError('La fecha de cierre no puede ser anterior a la de inicio.')
      return
    }
    setGuardando(true)
    setError(null)
    try {
      await alGuardar(form)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible guardar el proyecto.')
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{titulo}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{descripcion}</p>
      </header>

      <section className="card space-y-4 p-6">
        <div>
          <label className="label" htmlFor="titulo">Título</label>
          <input id="titulo" required minLength={5} maxLength={200} className="input" value={form.titulo} onChange={(e) => set('titulo', e.target.value)} />
        </div>

        <div>
          <label className="label" htmlFor="resumen">Resumen (una línea)</label>
          <input id="resumen" required minLength={10} maxLength={160} className="input" value={form.resumen} onChange={(e) => set('resumen', e.target.value)} />
        </div>

        <div>
          <label className="label" htmlFor="descripcion">Descripción</label>
          <textarea id="descripcion" rows={5} className="input" value={form.descripcion} onChange={(e) => set('descripcion', e.target.value)} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="area">Área</label>
            <select id="area" className="input" value={form.area} onChange={(e) => set('area', e.target.value as Area)}>
              {(areas.includes(form.area) ? areas : [form.area, ...areas]).map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="estado">Estado</label>
            <select id="estado" className="input" value={form.estado} onChange={(e) => set('estado', e.target.value as Estado)}>
              {ESTADOS.map((e) => <option key={e} value={e}>{ESTADO_LABEL[e]}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="lider">Líder</label>
            <input id="lider" className="input" maxLength={150} placeholder={usuario ? `Vacío = ${usuario.nombre}` : ''} value={form.lider} onChange={(e) => set('lider', e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="presupuesto">Presupuesto (COP)</label>
            <input id="presupuesto" type="number" min={0} step={100000} className="input" value={form.presupuesto} onChange={(e) => set('presupuesto', Number(e.target.value))} />
          </div>
          <div>
            <label className="label" htmlFor="avance">Avance (%)</label>
            <input id="avance" type="number" min={0} max={100} className="input" value={form.avance} onChange={(e) => set('avance', Number(e.target.value))} />
          </div>
          <div>
            <label className="label" htmlFor="equipo">Equipo (separado por comas)</label>
            <input id="equipo" className="input" value={form.equipo} onChange={(e) => set('equipo', e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="inicio">Fecha de inicio</label>
            <input id="inicio" type="date" required className="input" value={form.fecha_inicio} onChange={(e) => set('fecha_inicio', e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="fin">Fecha de cierre (opcional)</label>
            <input id="fin" type="date" className="input" min={form.fecha_inicio} value={form.fecha_fin} onChange={(e) => set('fecha_fin', e.target.value)} />
          </div>
        </div>

        <div>
          <label className="label" htmlFor="necesidades">¿Qué necesita? (perfiles, financiación, equipos…)</label>
          <textarea id="necesidades" rows={3} className="input" value={form.necesidades} onChange={(e) => set('necesidades', e.target.value)} />
        </div>

        <fieldset>
          <legend className="label">Objetivos de Desarrollo Sostenible</legend>
          <div className="flex flex-wrap gap-1.5">
            {ods.map((o) => {
              const activo = form.ods.includes(o.id)
              return (
                <button
                  key={o.id}
                  type="button"
                  aria-pressed={activo}
                  title={o.nombre}
                  onClick={() => set('ods', activo ? form.ods.filter((n) => n !== o.id) : [...form.ods, o.id].sort((a, b) => a - b))}
                  className={`rounded-full border px-2.5 py-1 text-xs transition ${
                    activo
                      ? 'border-brand-600 bg-brand-600 text-white dark:border-brand-400 dark:bg-brand-500'
                      : 'border-slate-300 text-slate-600 hover:border-brand-400 dark:border-slate-700 dark:text-slate-400'
                  }`}
                >
                  {o.id}. {o.nombre}
                </button>
              )
            })}
          </div>
        </fieldset>

        <div>
          <label className="label" htmlFor="etiquetas">Etiquetas (separadas por comas)</label>
          <input id="etiquetas" className="input" placeholder="IoT, agua, sensores" value={form.etiquetas} onChange={(e) => set('etiquetas', e.target.value)} />
        </div>

        {error && <p className="text-sm text-rose-600 dark:text-rose-400" role="alert">{error}</p>}

        <div className="flex flex-wrap justify-end gap-2 pt-2">
          {acciones?.(() => setForm(inicial))}
          <button type="submit" className="btn-primary" disabled={guardando}>
            {guardando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Save size={15} aria-hidden />}
            {guardando ? 'Guardando…' : textoBoton}
          </button>
        </div>
      </section>
    </form>
  )
}
