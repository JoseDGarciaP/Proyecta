import { useState } from 'react'
import { Check, CheckCircle2, Copy, Lightbulb, Loader2, Sparkles, ThumbsDown, ThumbsUp, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  aceptarRecomendacion, analizarProyecto, anularRecomendacion, redactarPitch, valorarDiagnostico, verValoraciones,
  type Recomendacion, type RespuestaIA, type RespuestaPitch, type Valoraciones,
} from '@/lib/ai'
import type { Oportunidad, Proyecto } from '@/lib/types'
import { useSesion } from '@/lib/sesion'
import { tienePanel } from '@/lib/permisos'
import { formatDate } from '@/lib/format'
import { apiHabilitada } from '@/lib/http'

/** Colores del estado de una recomendación guardada (HU-05). */
const ESTADO_REC_CLASS: Record<'pendiente' | 'aceptada' | 'anulada', string> = {
  pendiente: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  aceptada: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  anulada: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
}

export function PanelIA({ proyecto, oportunidades, esEquipo = false }: { proyecto: Proyecto; oportunidades: Oportunidad[]; esEquipo?: boolean }) {
  const [respuesta, setRespuesta] = useState<RespuestaIA | null>(null)
  const [valoraciones, setValoraciones] = useState<Valoraciones | null>(null)
  const [avisoRec, setAvisoRec] = useState('')
  const [cargando, setCargando] = useState(false)
  const [pitches, setPitches] = useState<Record<string, RespuestaPitch>>({})
  const [generandoPitch, setGenerandoPitch] = useState<string | null>(null)
  const [copiadoId, setCopiadoId] = useState<string | null>(null)
  const esAdmin = tienePanel(useSesion().usuario)

  const ejecutar = async () => {
    setCargando(true)
    try {
      setRespuesta(await analizarProyecto(proyecto, oportunidades))
      if (apiHabilitada) verValoraciones(proyecto.id).then(setValoraciones).catch(() => setValoraciones(null))
    } finally {
      setCargando(false)
    }
  }

  const pedirPitch = async (oportunidadId: string, tituloOportunidad: string) => {
    setGenerandoPitch(oportunidadId)
    try {
      const op = oportunidades.find((o) => o.id === oportunidadId) ?? {
        id: oportunidadId,
        titulo: tituloOportunidad,
        entidad: 'la entidad convocante',
      }
      const res = await redactarPitch(proyecto.id, op, proyecto.titulo)
      setPitches((prev) => ({ ...prev, [oportunidadId]: res }))
    } finally {
      setGenerandoPitch(null)
    }
  }

  const copiarPitch = async (oportunidadId: string, texto: string) => {
    try {
      await navigator.clipboard.writeText(texto)
      setCopiadoId(oportunidadId)
      window.setTimeout(() => setCopiadoId((actual) => (actual === oportunidadId ? null : actual)), 2000)
    } catch {
      // ignorar si el navegador restringe el portapapeles
    }
  }

  const cambiarEstado = (r: Recomendacion, estado: 'aceptada' | 'anulada') =>
    setRespuesta((x) => x && ({
      ...x,
      recomendaciones: x.recomendaciones.map((y) => (y.oportunidad_id === r.oportunidad_id ? { ...y, estado } : y)),
    }))

  const decidir = async (r: Recomendacion, accion: 'aceptar' | 'anular') => {
    if (!r.recomendacion_id) return
    setAvisoRec('')
    try {
      if (accion === 'aceptar') {
        await aceptarRecomendacion(r.recomendacion_id)
        cambiarEstado(r, 'aceptada')
      } else {
        const motivo = window.prompt('¿Por qué descartas esta oportunidad? No se volverá a sugerir.')?.trim()
        if (!motivo) return
        if (motivo.length < 5) {
          setAvisoRec('Escribe un motivo de al menos 5 caracteres.')
          return
        }
        await anularRecomendacion(r.recomendacion_id, motivo)
        cambiarEstado(r, 'anulada')
      }
    } catch (e) {
      setAvisoRec(e instanceof Error ? e.message : 'No se pudo guardar')
    }
  }

  const valorar = (util: boolean) => valorarDiagnostico(proyecto.id, util).then(setValoraciones).catch(() => {})

  const fortalezas = respuesta?.fortalezas ?? []
  const pasos = respuesta?.pasos_sugeridos ?? []

  return (
    <section className="card no-print p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <Sparkles size={16} className="text-brand-600 dark:text-brand-400" aria-hidden />
          Asistente de articulación y copiloto IA
        </h2>
        <button className="btn-primary" onClick={ejecutar} disabled={cargando}>
          {cargando ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Sparkles size={15} aria-hidden />}
          {cargando ? 'Analizando…' : 'Analizar'}
        </button>
      </div>

      {!respuesta && !cargando && (
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
          Genera un resumen ejecutivo, evalúa la madurez de la formulación del proyecto y sugiere oportunidades afines con borradores de postulación.
        </p>
      )}

      {respuesta && (
        <div className="mt-4 space-y-4">
          <div>
            <p className="label">Resumen ejecutivo</p>
            <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">{respuesta.resumen}</p>
          </div>

          {(fortalezas.length > 0 || pasos.length > 0) && (
            <div className="grid gap-3 sm:grid-cols-2">
              {fortalezas.length > 0 && (
                <div className="rounded-lg border border-emerald-200/80 bg-emerald-50/50 p-3.5 dark:border-emerald-500/20 dark:bg-emerald-500/5">
                  <p className="flex items-center gap-1.5 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
                    <CheckCircle2 size={14} aria-hidden /> Fortalezas de la ficha
                  </p>
                  <ul className="mt-2 space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                    {fortalezas.map((f, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" aria-hidden />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {pasos.length > 0 && (
                <div className="rounded-lg border border-amber-200/80 bg-amber-50/50 p-3.5 dark:border-amber-500/20 dark:bg-amber-500/5">
                  <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-800 dark:text-amber-300">
                    <Lightbulb size={14} aria-hidden /> Recomendaciones de formulación
                  </p>
                  <ul className="mt-2 space-y-1.5 text-xs text-slate-700 dark:text-slate-300">
                    {pasos.map((p, idx) => (
                      <li key={idx} className="flex items-start gap-1.5">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-amber-500" aria-hidden />
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {(respuesta.similares?.length ?? 0) > 0 && (
            <div>
              <p className="label">Proyectos similares en que se basan las sugerencias</p>
              <ul className="flex flex-wrap gap-2 text-xs">
                {respuesta.similares!.map((s) => (
                  <li key={s.id}>
                    <Link to={`/proyectos/${s.id}`} className="rounded-full border border-slate-200 px-2.5 py-1 hover:border-brand-400 dark:border-slate-700">
                      {s.titulo} · {Math.round(s.similitud * 100)} %
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {apiHabilitada && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span>¿Te sirvieron estas sugerencias?</span>
              <button type="button" aria-pressed={valoraciones?.mia === true} onClick={() => valorar(true)}
                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 ${valoraciones?.mia === true ? 'border-emerald-500 text-emerald-700' : 'border-slate-300 dark:border-slate-700'}`}>
                <ThumbsUp size={12} aria-hidden /> Útil {valoraciones ? `(${valoraciones.utiles})` : ''}
              </button>
              <button type="button" aria-pressed={valoraciones?.mia === false} onClick={() => valorar(false)}
                className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 ${valoraciones?.mia === false ? 'border-rose-500 text-rose-700' : 'border-slate-300 dark:border-slate-700'}`}>
                <ThumbsDown size={12} aria-hidden /> No útil {valoraciones ? `(${valoraciones.no_utiles})` : ''}
              </button>
            </div>
          )}

          {respuesta.recomendaciones.length > 0 && (
            <div>
              <p className="label">Oportunidades sugeridas</p>
              <ul className="space-y-2.5">
                {respuesta.recomendaciones.map((r) => {
                  const pitch = pitches[r.oportunidad_id]
                  const cargandoEste = generandoPitch === r.oportunidad_id
                  return (
                    <li
                      key={r.oportunidad_id}
                      className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-800"
                    >
                      <div className="flex flex-wrap items-baseline justify-between gap-3">
                        <span className="font-medium text-slate-800 dark:text-slate-100">{r.titulo}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 tabular-nums dark:text-slate-400">
                            afinidad {Math.round(r.puntaje * 100)}%
                          </span>
                          <button
                            type="button"
                            className="btn-ghost px-2.5 py-1 text-xs"
                            disabled={cargandoEste}
                            onClick={() => pedirPitch(r.oportunidad_id, r.titulo)}
                          >
                            {cargandoEste ? (
                              <Loader2 size={13} className="animate-spin" aria-hidden />
                            ) : (
                              <Sparkles size={13} className="text-brand-600 dark:text-brand-400" aria-hidden />
                            )}
                            {pitch ? 'Regenerar pitch' : 'Borrador de postulación'}
                          </button>
                        </div>
                      </div>
                      <p className="mt-1 text-slate-600 dark:text-slate-400">{r.razon}</p>
                      {r.estado && (
                        <p className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                          <span className={`rounded-full px-2 py-0.5 font-medium ${ESTADO_REC_CLASS[r.estado]}`}>{r.estado}</span>
                          {r.fecha && <span>Recomendada el {formatDate(r.fecha)}</span>}
                          {esEquipo && r.recomendacion_id && r.estado === 'pendiente' && (
                            <>
                              <button type="button" className="inline-flex items-center gap-1 text-emerald-700 hover:underline dark:text-emerald-400" onClick={() => decidir(r, 'aceptar')}>
                                <Check size={12} aria-hidden /> Aceptar
                              </button>
                              <button type="button" className="inline-flex items-center gap-1 text-slate-600 hover:underline dark:text-slate-400" onClick={() => decidir(r, 'anular')}>
                                <X size={12} aria-hidden /> Descartar
                              </button>
                            </>
                          )}
                        </p>
                      )}

                      {pitch && (
                        <div className="mt-3 rounded-md border border-brand-200/70 bg-brand-50/40 p-3 dark:border-brand-500/20 dark:bg-brand-500/5">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs font-semibold text-brand-800 dark:text-brand-200">
                              Borrador sugerido para postular
                            </span>
                            <button
                              type="button"
                              className="inline-flex items-center gap-1 text-xs font-medium text-brand-700 hover:underline dark:text-brand-300"
                              onClick={() => copiarPitch(r.oportunidad_id, pitch.pitch)}
                            >
                              {copiadoId === r.oportunidad_id ? <Check size={13} aria-hidden /> : <Copy size={13} aria-hidden />}
                              {copiadoId === r.oportunidad_id ? 'Copiado' : 'Copiar texto'}
                            </button>
                          </div>
                          <p className="mt-1.5 text-xs leading-relaxed text-slate-700 dark:text-slate-200">{pitch.pitch}</p>
                        </div>
                      )}
                    </li>
                  )
                })}
              </ul>
            </div>
          )}

          {avisoRec && <p role="alert" className="text-xs text-red-600">{avisoRec}</p>}

          {respuesta.simulado && (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Resumen automático básico: el asistente de IA no está disponible en este momento.
              {esAdmin && ' (Solo administradores: configura el proveedor de IA del servidor para que lo redacte un modelo).'}
            </p>
          )}
        </div>
      )}
    </section>
  )
}
