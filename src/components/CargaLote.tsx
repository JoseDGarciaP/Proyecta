import { useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, FileSpreadsheet, Info, Loader2, RefreshCw, Upload, UserCheck, UserPlus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { confirmarLote, previaLote, revisarLote } from '@/lib/admin'
import { useAreas } from '@/lib/parametros'
import { ESTADOS, ESTADO_LABEL, type Estado, type FilaLote, type ResultadoLote } from '@/lib/types'
import { RESUMEN_MAX } from './FormularioProyecto'
import { Badge } from './ui'

/**
 * Carga de proyectos por lote: el admin sube el Excel de respuestas del formulario de registro, revisa cada
 * fila (cuenta nueva / existente / con problemas), corrige lo necesario y confirma. La API valida otra vez
 * todo al confirmar y no guarda nada si alguna fila incluida tiene errores.
 */
export function CargaLote() {
  const [filas, setFilas] = useState<FilaLote[] | null>(null)
  const [archivo, setArchivo] = useState<string>('')
  const [cargando, setCargando] = useState<'' | 'leyendo' | 'revisando' | 'confirmando'>('')
  const [error, setError] = useState<string | null>(null)
  const [resultado, setResultado] = useState<ResultadoLote | null>(null)
  const [abierta, setAbierta] = useState<number | null>(null)
  const [editadas, setEditadas] = useState(false)
  const entrada = useRef<HTMLInputElement>(null)

  const ejecutar = async <T,>(fase: typeof cargando, accion: () => Promise<T>): Promise<T | undefined> => {
    setCargando(fase)
    setError(null)
    try {
      return await accion()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Algo falló. Intenta de nuevo.')
    } finally {
      setCargando('')
    }
  }

  const leer = async (f: File | undefined) => {
    if (!f) return
    setResultado(null)
    setArchivo(f.name)
    const leidas = await ejecutar('leyendo', () => previaLote(f))
    if (leidas) {
      setFilas(leidas)
      setEditadas(false)
      setAbierta(null)
    }
    if (entrada.current) entrada.current.value = ''
  }

  const cambiar = (fila: number, cambios: Partial<FilaLote>) => {
    setFilas((xs) => xs?.map((x) => (x.fila === fila ? { ...x, ...cambios } : x)) ?? null)
    setEditadas(true)
  }

  const revisar = async () => {
    if (!filas) return
    const revisadas = await ejecutar('revisando', () => revisarLote(filas))
    if (revisadas) {
      setFilas(revisadas)
      setEditadas(false)
    }
  }

  const confirmar = async () => {
    if (!filas) return
    const r = await ejecutar('confirmando', () => confirmarLote(filas))
    if (r) {
      setResultado(r)
      setFilas(null)
    }
  }

  const incluidas = filas?.filter((f) => f.incluir) ?? []
  const conError = incluidas.filter((f) => f.errores.length > 0)
  const nuevas = new Set(incluidas.filter((f) => f.cuenta === 'nueva').map((f) => f.correo)).size
  const existentes = new Set(incluidas.filter((f) => f.cuenta === 'existente').map((f) => f.correo)).size
  const listo = filas && incluidas.length > 0 && conError.length === 0 && !editadas

  if (resultado) {
    return (
      <div className="card space-y-3 p-6 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600 dark:text-emerald-400" />
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Carga completada</h2>
        <p className="text-sm text-slate-600 dark:text-slate-300">
          Se registraron {resultado.proyectos} proyectos. Cuentas nuevas: {resultado.cuentas_nuevas}. Cuentas que ya existían:{' '}
          {resultado.cuentas_existentes}. Se enviaron {resultado.correos} correos, uno por persona.
        </p>
        <div className="flex justify-center gap-2">
          <Link to="/proyectos" className="btn-primary">Ver proyectos</Link>
          <button type="button" className="btn-ghost" onClick={() => setResultado(null)}>Cargar otro archivo</button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="card space-y-3 p-5">
        <div className="flex items-start gap-3">
          <FileSpreadsheet className="mt-0.5 h-5 w-5 shrink-0 text-brand-600 dark:text-brand-300" />
          <div className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
            <p>
              Sube el Excel (.xlsx) de respuestas del formulario de registro de proyectos, con sus mismas columnas. Antes de
              guardar verás cada fila para revisarla.
            </p>
            <p className="text-slate-500 dark:text-slate-400">
              Por cada correo nuevo se crea una cuenta de estudiante y se envía un solo correo para elegir la contraseña (el
              enlace dura 7 días). A quien ya tiene cuenta se le avisa que se registró un proyecto a su nombre. El avance se
              ajusta según el estado, se quita al líder de los coautores y los proyectos de Educación reciben el ODS 4.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={entrada}
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            className="hidden"
            onChange={(e) => leer(e.target.files?.[0])}
          />
          <button type="button" className="btn-primary" disabled={cargando !== ''} onClick={() => entrada.current?.click()}>
            {cargando === 'leyendo' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            {filas ? 'Subir otro archivo' : 'Elegir archivo'}
          </button>
          {archivo && <span className="text-sm text-slate-500 dark:text-slate-400">{archivo}</span>}
        </div>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </p>
      )}

      {filas && (
        <>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <Badge className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200">{incluidas.length} de {filas.length} filas incluidas</Badge>
            <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">{nuevas} cuentas nuevas</Badge>
            <Badge className="bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300">{existentes} cuentas existentes</Badge>
            {conError.length > 0 && (
              <Badge className="bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300">{conError.length} con problemas</Badge>
            )}
          </div>

          <ul className="space-y-2">
            {filas.map((f) => (
              <FilaVista
                key={f.fila}
                fila={f}
                abierta={abierta === f.fila}
                alternar={() => setAbierta(abierta === f.fila ? null : f.fila)}
                cambiar={(c) => cambiar(f.fila, c)}
              />
            ))}
          </ul>

          <div className="sticky bottom-0 flex flex-wrap items-center justify-end gap-3 border-t border-slate-200 bg-white/90 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
            {editadas && <span className="text-sm text-amber-700 dark:text-amber-300">Hay cambios sin revisar</span>}
            {!editadas && conError.length > 0 && (
              <span className="text-sm text-red-700 dark:text-red-300">Corrige o excluye las filas con problemas para continuar</span>
            )}
            <button type="button" className="btn-ghost" disabled={cargando !== ''} onClick={revisar}>
              {cargando === 'revisando' ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Revisar de nuevo
            </button>
            <button type="button" className="btn-primary" disabled={!listo || cargando !== ''} onClick={confirmar}>
              {cargando === 'confirmando' ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              Confirmar carga ({incluidas.length})
            </button>
          </div>
        </>
      )}
    </div>
  )
}

function FilaVista({ fila: f, abierta, alternar, cambiar }: {
  fila: FilaLote
  abierta: boolean
  alternar: () => void
  cambiar: (c: Partial<FilaLote>) => void
}) {
  const areas = useAreas()
  const problemas = f.incluir && f.errores.length > 0
  const borde = !f.incluir
    ? 'opacity-60'
    : problemas ? 'ring-1 ring-red-300 dark:ring-red-800' : ''

  return (
    <li className={`card p-0 ${borde}`}>
      <div className="flex items-start gap-3 p-4">
        <input
          type="checkbox"
          className="mt-1 h-4 w-4 shrink-0 accent-brand-600"
          checked={f.incluir}
          onChange={(e) => cambiar({ incluir: e.target.checked })}
          aria-label={`Incluir fila ${f.fila}`}
        />
        <button type="button" className="min-w-0 flex-1 text-left" onClick={alternar} aria-expanded={abierta}>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs tabular-nums text-slate-400">Fila {f.fila}</span>
            {f.cuenta === 'nueva' && (
              <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"><UserPlus className="mr-1 h-3 w-3" />Cuenta nueva</Badge>
            )}
            {f.cuenta === 'existente' && (
              <Badge className="bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300"><UserCheck className="mr-1 h-3 w-3" />Ya tiene cuenta</Badge>
            )}
            {problemas && (
              <Badge className="bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300"><AlertTriangle className="mr-1 h-3 w-3" />Con problemas</Badge>
            )}
          </div>
          <p className="mt-1 truncate font-medium text-slate-900 dark:text-white">{f.titulo || '(sin título)'}</p>
          <p className="truncate text-sm text-slate-500 dark:text-slate-400">
            {f.nombre_cuenta} · {f.correo} · {f.area} · {ESTADO_LABEL[f.estado]} {f.avance} %
          </p>
          {f.incluir && f.errores.map((e) => (
            <p key={e} className="mt-1 flex gap-1.5 text-sm text-red-700 dark:text-red-300"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{e}</p>
          ))}
          {f.avisos.map((a) => (
            <p key={a} className="mt-1 flex gap-1.5 text-xs text-slate-500 dark:text-slate-400"><Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />{a}</p>
          ))}
        </button>
        <ChevronDown className={`mt-1 h-4 w-4 shrink-0 text-slate-400 transition-transform ${abierta ? 'rotate-180' : ''}`} />
      </div>

      {abierta && (
        <div className="grid gap-4 border-t border-slate-200 p-4 sm:grid-cols-2 dark:border-slate-800">
          <Campo etiqueta="Título" className="sm:col-span-2">
            <input className="input" maxLength={200} value={f.titulo} onChange={(e) => cambiar({ titulo: e.target.value })} />
          </Campo>
          <Campo etiqueta={`Resumen (${f.resumen.length}/${RESUMEN_MAX})`} className="sm:col-span-2">
            <textarea className="input" rows={3} value={f.resumen} onChange={(e) => cambiar({ resumen: e.target.value })} />
          </Campo>
          <Campo etiqueta="Correo de la cuenta">
            <input className="input" type="email" value={f.correo} onChange={(e) => cambiar({ correo: e.target.value })} />
          </Campo>
          <Campo etiqueta="Nombre de la cuenta">
            <input className="input" maxLength={150} value={f.nombre_cuenta} disabled={f.cuenta === 'existente'}
                   onChange={(e) => cambiar({ nombre_cuenta: e.target.value })} />
          </Campo>
          <Campo etiqueta="Líder del proyecto">
            <input className="input" maxLength={150} value={f.lider} onChange={(e) => cambiar({ lider: e.target.value })} />
          </Campo>
          <Campo etiqueta="Coautores (separados por coma)">
            <input className="input" value={f.equipo.join(', ')}
                   onChange={(e) => cambiar({ equipo: e.target.value.split(',').map((x) => x.trim()).filter(Boolean) })} />
          </Campo>
          <Campo etiqueta="Área">
            <select className="input" value={f.area} onChange={(e) => cambiar({ area: e.target.value })}>
              {(areas.includes(f.area) ? areas : [f.area, ...areas]).map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </Campo>
          <div className="grid grid-cols-2 gap-4">
            <Campo etiqueta="Estado">
              <select className="input" value={f.estado} onChange={(e) => cambiar({ estado: e.target.value as Estado })}>
                {ESTADOS.map((e) => <option key={e} value={e}>{ESTADO_LABEL[e]}</option>)}
              </select>
            </Campo>
            <Campo etiqueta="Avance %">
              <input className="input" type="number" min={0} max={100} value={f.avance}
                     onChange={(e) => cambiar({ avance: Math.max(0, Math.min(100, Number(e.target.value) || 0)) })} />
            </Campo>
          </div>
        </div>
      )}
    </li>
  )
}

function Campo({ etiqueta, className = '', children }: { etiqueta: string; className?: string; children: React.ReactNode }) {
  return (
    <label className={`block ${className}`}>
      <span className="label">{etiqueta}</span>
      {children}
    </label>
  )
}
