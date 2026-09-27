import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Save } from 'lucide-react'
import { crearProyecto } from '@/lib/api'
import { AREAS, ESTADOS, ESTADO_LABEL, ODS, type Area, type Estado } from '@/lib/types'
import { useSesion } from '@/lib/sesion'

const inicial = {
  titulo: '',
  resumen: '',
  descripcion: '',
  necesidades: '',
  area: AREAS[0] as Area,
  estado: 'idea' as Estado,
  avance: 0,
  presupuesto: 0,
  lider: '',
  equipo: '',
  etiquetas: '',
  fecha_inicio: new Date().toISOString().slice(0, 10),
  fecha_fin: '',
  ods: [] as number[],
}

export function NuevoProyecto() {
  const [form, setForm] = useState(inicial)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navegar = useNavigate()
  const { usuario } = useSesion()

  const set = <K extends keyof typeof form>(clave: K, valor: (typeof form)[K]) =>
    setForm((f) => ({ ...f, [clave]: valor }))

  const enviar = async (e: React.FormEvent) => {
    e.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      const creado = await crearProyecto({
        titulo: form.titulo.trim(),
        resumen: form.resumen.trim(),
        descripcion: form.descripcion.trim(),
        necesidades: form.necesidades.trim(),
        area: form.area,
        estado: form.estado,
        avance: Number(form.avance),
        presupuesto: Number(form.presupuesto),
        lider: form.lider.trim(),
        equipo: separar(form.equipo),
        etiquetas: separar(form.etiquetas),
        fecha_inicio: form.fecha_inicio,
        fecha_fin: form.fecha_fin || null,
        actores: [],
        ods: form.ods,
      })
      navegar(`/proyectos/${creado.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No fue posible guardar el proyecto.')
      setGuardando(false)
    }
  }

  return (
    <form onSubmit={enviar} className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Registrar proyecto</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          La información alimenta el panel de métricas y el motor de recomendaciones.
        </p>
      </header>

      <section className="card space-y-4 p-6">
        <div>
          <label className="label" htmlFor="titulo">Título</label>
          <input id="titulo" required className="input" value={form.titulo} onChange={(e) => set('titulo', e.target.value)} />
        </div>

        <div>
          <label className="label" htmlFor="resumen">Resumen (una línea)</label>
          <input id="resumen" required maxLength={160} className="input" value={form.resumen} onChange={(e) => set('resumen', e.target.value)} />
        </div>

        <div>
          <label className="label" htmlFor="descripcion">Descripción</label>
          <textarea id="descripcion" rows={5} className="input" value={form.descripcion} onChange={(e) => set('descripcion', e.target.value)} />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label" htmlFor="area">Área</label>
            <select id="area" className="input" value={form.area} onChange={(e) => set('area', e.target.value as Area)}>
              {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
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
            <input id="lider" className="input" placeholder={usuario ? `Vacío = ${usuario.nombre}` : ''} value={form.lider} onChange={(e) => set('lider', e.target.value)} />
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
            <input id="inicio" type="date" className="input" value={form.fecha_inicio} onChange={(e) => set('fecha_inicio', e.target.value)} />
          </div>
          <div>
            <label className="label" htmlFor="fin">Fecha de cierre (opcional)</label>
            <input id="fin" type="date" className="input" value={form.fecha_fin} onChange={(e) => set('fecha_fin', e.target.value)} />
          </div>
        </div>

        <div>
          <label className="label" htmlFor="necesidades">¿Qué necesita? (perfiles, financiación, equipos…)</label>
          <textarea id="necesidades" rows={3} className="input" value={form.necesidades} onChange={(e) => set('necesidades', e.target.value)} />
        </div>

        <fieldset>
          <legend className="label">Objetivos de Desarrollo Sostenible</legend>
          <div className="flex flex-wrap gap-1.5">
            {ODS.map((o) => {
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

        {error && <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-ghost" onClick={() => setForm(inicial)}>Limpiar</button>
          <button type="submit" className="btn-primary" disabled={guardando}>
            {guardando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Save size={15} aria-hidden />}
            {guardando ? 'Guardando…' : 'Guardar proyecto'}
          </button>
        </div>
      </section>
    </form>
  )
}

const separar = (valor: string) =>
  valor.split(',').map((v) => v.trim()).filter(Boolean)
