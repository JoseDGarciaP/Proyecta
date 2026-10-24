import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight, History, Info, PartyPopper, Sparkles, TrendingUp } from 'lucide-react'
import { formatoXP, miExperiencia, olvidarNivel } from '@/lib/experiencia'
import { listarAvisos, marcarAviso } from '@/lib/notificaciones'
import { useSesion } from '@/lib/sesion'
import type { MiExperiencia, Nivel, NivelBreve } from '@/lib/types'
import { Skeleton } from '@/components/ui'
import { Modal } from '@/components/Modal'
import { hace } from '@/components/IconoAviso'
import { Medalla } from '@/components/Insignia'

/** Medalla grande de un nivel con su número. */
export function MedallaNivel({ nivel, tamano = 'lg', apagada = false }: { nivel: NivelBreve | Nivel; tamano?: 'md' | 'lg'; apagada?: boolean }) {
  return (
    <span className="relative inline-block">
      <Medalla icono={nivel.icono} color={nivel.color} tamano={tamano} apagada={apagada} titulo={`Nivel ${nivel.posicion}: ${nivel.nombre}`} />
      <span className="absolute -right-1 -bottom-1 grid h-5 min-w-5 place-items-center rounded-full bg-slate-900 px-1 text-[10px] font-bold text-white tabular-nums ring-2 ring-white dark:bg-white dark:text-slate-900 dark:ring-slate-900">
        {nivel.posicion}
      </span>
    </span>
  )
}

/** Avance hacia el siguiente nivel en XP (0–100). */
function porcentaje(d: MiExperiencia): number {
  if (!d.siguiente) return 100
  const meta = d.siguiente.nivel.xp_minima
  return meta <= 0 ? 100 : Math.min(100, Math.round((d.xp / meta) * 100))
}

/** «Mi nivel» del perfil: nivel actual, qué falta para el siguiente, historial de XP y cómo ganar más. */
export function MiNivel({ version }: { version?: unknown }) {
  const [datos, setDatos] = useState<MiExperiencia | null>(null)
  const [error, setError] = useState('')
  const [pestana, setPestana] = useState<'historial' | 'ganar'>('historial')
  const [verTodo, setVerTodo] = useState(false)

  useEffect(() => {
    miExperiencia().then(setDatos).catch((e: Error) => setError(e.message))
  }, [version])

  useEffect(() => {
    if (datos && window.location.hash === '#nivel') document.getElementById('nivel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [datos])

  if (error) return <section id="nivel" className="card p-5 text-sm text-rose-600">{error}</section>
  if (!datos) return <Skeleton className="h-56" />

  const sig = datos.siguiente
  const historial = verTodo ? datos.historial : datos.historial.slice(0, 6)

  return (
    <section id="nivel" className="card scroll-mt-24 overflow-hidden">
      <div className="flex flex-wrap items-center gap-5 bg-gradient-to-r from-brand-50 to-transparent p-5 dark:from-brand-500/10">
        {datos.nivel && <MedallaNivel nivel={datos.nivel} />}
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
            Nivel {datos.nivel?.posicion ?? 1} de {datos.total_niveles}
          </p>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">{datos.nivel?.nombre ?? 'Sin nivel'}</h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            <b className="tabular-nums">{formatoXP(datos.xp)}</b>
            {datos.xp_semana > 0 && <span className="text-emerald-700 dark:text-emerald-400"> · +{datos.xp_semana} esta semana</span>}
          </p>
        </div>
        <Link to="/logros#ranking-xp" className="btn-ghost text-sm">
          <TrendingUp size={15} aria-hidden /> Ranking
        </Link>
      </div>

      <div className="space-y-5 p-5">
        {sig ? (
          <div>
            <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
              <span className="text-slate-600 dark:text-slate-300">
                Siguiente: <b className="text-slate-900 dark:text-white">{sig.nivel.nombre}</b>
              </span>
              <span className="text-xs text-slate-500 tabular-nums">{datos.xp.toLocaleString('es-CO')} / {sig.nivel.xp_minima.toLocaleString('es-CO')} XP</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="progressbar"
              aria-valuenow={porcentaje(datos)} aria-valuemin={0} aria-valuemax={100} aria-label={`Avance hacia ${sig.nivel.nombre}`}>
              <div className="h-full rounded-full bg-brand-600 transition-[width] duration-700 dark:bg-brand-400" style={{ width: `${porcentaje(datos)}%` }} />
            </div>
            <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600 dark:text-slate-400">
              {sig.xp_faltante > 0 && <li>Te faltan <b className="tabular-nums">{formatoXP(sig.xp_faltante)}</b></li>}
              {sig.insignias_faltantes > 0 && (
                <li>
                  y <b className="tabular-nums">{sig.insignias_faltantes}</b> {sig.insignias_faltantes === 1 ? 'insignia' : 'insignias'} más (<a href="#logros" className="underline">ver logros</a>)
                </li>
              )}
              {sig.requeridas_faltantes.length > 0 && <li>Necesitas: {sig.requeridas_faltantes.join(', ')}</li>}
              {sig.xp_faltante <= 0 && sig.insignias_faltantes <= 0 && !sig.requeridas_faltantes.length && <li>¡Ya casi! Se actualiza en un momento.</li>}
            </ul>
          </div>
        ) : (
          <p className="flex items-center gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
            <Sparkles size={15} aria-hidden /> Llegaste al nivel más alto. ¡Felicitaciones!
          </p>
        )}

        <div>
          <div role="tablist" className="mb-3 flex gap-1 border-b border-slate-200 dark:border-slate-800">
            {([['historial', 'Historial', History], ['ganar', 'Cómo ganar XP', Info]] as const).map(([clave, texto, Icono]) => (
              <button key={clave} role="tab" aria-selected={pestana === clave} onClick={() => setPestana(clave)}
                className={`-mb-px inline-flex items-center gap-1.5 border-b-2 px-3 py-2 text-sm font-medium ${pestana === clave
                  ? 'border-brand-600 text-brand-700 dark:border-brand-400 dark:text-brand-300'
                  : 'border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}`}>
                <Icono size={14} aria-hidden /> {texto}
              </button>
            ))}
          </div>

          {pestana === 'historial' ? (
            datos.historial.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">Aún no tienes movimientos. Completa tu perfil o registra un proyecto para empezar.</p>
            ) : (
              <>
                <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                  {historial.map((m) => (
                    <li key={m.id} className="flex items-start gap-3 py-2 text-sm">
                      <span className={`mt-0.5 w-14 shrink-0 text-right font-semibold tabular-nums ${m.puntos >= 0 ? 'text-emerald-700 dark:text-emerald-400' : 'text-rose-700 dark:text-rose-400'}`}>
                        {m.puntos >= 0 ? '+' : ''}{m.puntos}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-slate-800 dark:text-slate-200">{m.accion_nombre}</p>
                        {((m.detalle && m.detalle !== m.accion_nombre) || m.otorgado_por) && (
                          <p className="truncate text-xs text-slate-500 dark:text-slate-400" title={m.detalle}>
                            {m.detalle !== m.accion_nombre && m.detalle}{m.otorgado_por && `${m.detalle !== m.accion_nombre && m.detalle ? ' · ' : ''}por ${m.otorgado_por}`}
                          </p>
                        )}
                      </div>
                      <span className="shrink-0 text-xs text-slate-400">{hace(m.creado_en)}</span>
                    </li>
                  ))}
                </ul>
                {datos.historial.length > 6 && (
                  <button className="mt-2 text-sm text-brand-700 hover:underline dark:text-brand-300" onClick={() => setVerTodo((x) => !x)}>
                    {verTodo ? 'Ver menos' : `Ver los ${datos.historial.length} movimientos`}
                  </button>
                )}
              </>
            )
          ) : (
            <ul className="grid gap-2 sm:grid-cols-2">
              {datos.acciones.filter((a) => a.activo && a.puntos > 0).map((a) => (
                <li key={a.clave} className="flex items-start gap-3 rounded-lg border border-slate-200 p-2.5 dark:border-slate-800">
                  <span className="rounded-md bg-brand-50 px-1.5 py-0.5 text-xs font-semibold text-brand-700 tabular-nums dark:bg-brand-500/15 dark:text-brand-300">
                    +{a.puntos}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-800 dark:text-slate-200">{a.nombre}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      {a.descripcion}{a.tope_diario ? ` Hasta ${a.tope_diario} ${a.tope_diario === 1 ? 'vez' : 'veces'} al día.` : ''}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}

const CLAVE_VISTOS = 'proyecta_niveles_vistos'

function vistos(): string[] {
  try {
    return JSON.parse(localStorage.getItem(CLAVE_VISTOS) || '[]')
  } catch {
    return []
  }
}

function recordar(ids: string[]) {
  try {
    localStorage.setItem(CLAVE_VISTOS, JSON.stringify([...vistos(), ...ids].slice(-30)))
  } catch {
    /* sin almacenamiento: puede volver a mostrarse */
  }
}

/**
 * Celebración al subir de nivel. Se dispara con los avisos «nivel» sin leer (llegan por la campana),
 * una sola vez por aviso. `total` = avisos sin leer, para revisar cuando cambia.
 */
export function CelebracionNivel({ total }: { total: number }) {
  const { usuario } = useSesion()
  const [celebrar, setCelebrar] = useState<{ avisos: string[]; datos: MiExperiencia } | null>(null)

  useEffect(() => {
    if (!usuario || total <= 0 || celebrar) return
    let vivo = true
    listarAvisos(true, 15)
      .then(async (avisos) => {
        const yaVistos = vistos()
        // Si subió varios niveles de una vez, se celebra una sola vez (con el nivel actual).
        const nuevos = avisos.filter((a) => a.tipo === 'nivel' && a.titulo.startsWith('¡Subiste') && !yaVistos.includes(a.id)).map((a) => a.id)
        if (!nuevos.length) return
        olvidarNivel(usuario.id)
        const datos = await miExperiencia()
        if (vivo) setCelebrar({ avisos: nuevos, datos })
      })
      .catch(() => {})
    return () => {
      vivo = false
    }
  }, [total, usuario, celebrar])

  if (!celebrar) return null
  const { datos, avisos } = celebrar
  const cerrar = () => {
    recordar(avisos)
    avisos.forEach((id) => marcarAviso(id).catch(() => {}))
    setCelebrar(null)
  }

  return (
    <Modal titulo="¡Subiste de nivel!" alCerrar={cerrar} ancho="max-w-sm">
      <div className="flex flex-col items-center text-center">
        <div className="relative my-2">
          <span className="absolute inset-0 animate-ping rounded-full bg-amber-300/40 motion-reduce:hidden" aria-hidden />
          {datos.nivel && <MedallaNivel nivel={datos.nivel} />}
        </div>
        <p className="mt-3 flex items-center gap-1.5 text-lg font-semibold text-slate-900 dark:text-white">
          <PartyPopper size={18} className="text-amber-500" aria-hidden /> Ahora eres {datos.nivel?.nombre}
        </p>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Nivel {datos.nivel?.posicion} de {datos.total_niveles} · {formatoXP(datos.xp)}
        </p>
        {datos.siguiente && (
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Próximo: <b>{datos.siguiente.nivel.nombre}</b>
            {datos.siguiente.xp_faltante > 0 && <> · faltan {formatoXP(datos.siguiente.xp_faltante)}</>}
          </p>
        )}
        <div className="mt-5 flex w-full gap-2">
          <button className="btn-ghost flex-1" onClick={cerrar}>Cerrar</button>
          <Link to="/perfil#nivel" className="btn-primary flex-1" onClick={cerrar}>
            Ver mi nivel <ChevronRight size={15} aria-hidden />
          </Link>
        </div>
      </div>
    </Modal>
  )
}

/** Escalera de niveles (página de logros). */
export function CaminoNiveles({ niveles, actual }: { niveles: Nivel[]; actual?: number | null }) {
  const nombres = (n: Nivel) => [
    `${n.xp_minima.toLocaleString('es-CO')} XP`,
    n.insignias_minimas ? `${n.insignias_minimas} ${n.insignias_minimas === 1 ? 'insignia' : 'insignias'}` : '',
    n.insignias_requeridas.length ? `${n.insignias_requeridas.length} obligatoria${n.insignias_requeridas.length === 1 ? '' : 's'}` : '',
  ].filter(Boolean).join(' · ')
  return (
    <ol className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {niveles.map((n) => {
        const alcanzado = actual != null && n.posicion <= actual
        const esActual = actual === n.posicion
        return (
          <li key={n.id} className={`flex items-center gap-3 rounded-lg border p-3 ${esActual
            ? 'border-brand-400 bg-brand-50/60 dark:border-brand-500/50 dark:bg-brand-500/10' : 'border-slate-200 dark:border-slate-800'}`}>
            <MedallaNivel nivel={n} tamano="md" apagada={actual != null && !alcanzado} />
            <div className="min-w-0">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-slate-900 dark:text-white">
                {n.nombre}
                {esActual && <span className="rounded-full bg-brand-600 px-1.5 py-px text-[10px] font-medium text-white dark:bg-brand-400 dark:text-brand-950">Tú</span>}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">{nombres(n)}</p>
              <p className="text-[11px] text-slate-400">{n.personas} {n.personas === 1 ? 'persona' : 'personas'}</p>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
