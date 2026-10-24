import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Medal, Mountain, Trophy } from 'lucide-react'
import { catalogoInsignias, ranking } from '@/lib/insignias'
import { listarNiveles, miExperiencia, rankingXP } from '@/lib/experiencia'
import { apiHabilitada } from '@/lib/http'
import { usePuede } from '@/lib/permisos'
import { useSesion } from '@/lib/sesion'
import type { Insignia, Nivel, PuestoRanking, PuestoXP, TipoInsignia } from '@/lib/types'
import { EmptyState, Skeleton } from '@/components/ui'
import { FilaInsignias, Medalla, NivelChip, TIPO_CLASE, TIPO_LABEL } from '@/components/Insignia'
import { CaminoNiveles } from '@/components/Nivel'

const PODIO = ['text-amber-500', 'text-slate-400', 'text-orange-700']
type Vista = 'semana' | 'mes' | 'siempre' | 'insignias'
const VISTAS: [Vista, string][] = [['semana', 'Semana'], ['mes', 'Mes'], ['siempre', 'Siempre'], ['insignias', 'Insignias']]

function Puesto({ posicion }: { posicion: number }) {
  return (
    <span className="w-7 text-center text-sm font-semibold tabular-nums text-slate-500">
      {posicion <= 3 ? <Medal size={18} className={`mx-auto ${PODIO[posicion - 1]}`} aria-label={`Puesto ${posicion}`} /> : posicion}
    </span>
  )
}

/** Niveles, ranking (por XP o por insignias) y catálogo de cómo ganar cada insignia. */
export function Logros() {
  const puede = usePuede()
  const { usuario } = useSesion()
  const [vista, setVista] = useState<Vista>('semana')
  const [porXP, setPorXP] = useState<PuestoXP[] | null>(null)
  const [porInsignias, setPorInsignias] = useState<PuestoRanking[] | null>(null)
  const [insignias, setInsignias] = useState<Insignia[] | null>(null)
  const [niveles, setNiveles] = useState<Nivel[] | null>(null)
  const [miPosicion, setMiPosicion] = useState<number | null>(null)
  const [tipo, setTipo] = useState<TipoInsignia | 'todas'>('todas')
  const verRanking = puede('usuarios.ver')

  useEffect(() => {
    if (!apiHabilitada) return
    catalogoInsignias().then(setInsignias).catch(() => setInsignias([]))
    listarNiveles().then(setNiveles).catch(() => setNiveles([]))
    miExperiencia().then((e) => setMiPosicion(e.nivel?.posicion ?? null)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!apiHabilitada || !verRanking) return
    if (vista === 'insignias') {
      setPorInsignias(null)
      ranking(25).then(setPorInsignias).catch(() => setPorInsignias([]))
    } else {
      setPorXP(null)
      rankingXP(vista).then(setPorXP).catch(() => setPorXP([]))
    }
  }, [vista, verRanking])

  useEffect(() => {
    if (window.location.hash === '#ranking-xp') document.getElementById('ranking-xp')?.scrollIntoView({ block: 'start' })
  }, [])

  if (!apiHabilitada) return <EmptyState titulo="Los logros necesitan la API" detalle="Conecta el backend (VITE_API_URL) e ingresa con tu cuenta." />

  const cargando = vista === 'insignias' ? !porInsignias : !porXP
  const vacio = vista === 'insignias' ? porInsignias?.length === 0 : porXP?.length === 0

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Logros</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Gana experiencia participando en proyectos, convocatorias y equipos, sube de nivel y consigue insignias. Lo tuyo está en{' '}
          <Link to="/perfil#nivel" className="text-brand-700 hover:underline dark:text-brand-300">tu perfil</Link>.
        </p>
      </header>

      <section className="card p-5">
        <h2 className="mb-1 flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
          <Mountain size={16} className="text-brand-600 dark:text-brand-400" aria-hidden /> Niveles
        </h2>
        <p className="mb-4 text-xs text-slate-500 dark:text-slate-400">
          Se suben en orden: cada nivel pide cierta experiencia y, desde los intermedios, también insignias.
        </p>
        {!niveles ? <Skeleton className="h-40" /> : <CaminoNiveles niveles={niveles} actual={miPosicion} />}
      </section>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {verRanking && (
          <section id="ranking-xp" className="card scroll-mt-24">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <h2 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white">
                <Trophy size={16} className="text-amber-500" aria-hidden /> Ranking
              </h2>
              <div role="tablist" aria-label="Periodo del ranking" className="inline-flex rounded-lg bg-slate-100 p-0.5 dark:bg-slate-800">
                {VISTAS.map(([v, texto]) => (
                  <button key={v} role="tab" aria-selected={vista === v} onClick={() => setVista(v)}
                    className={`rounded-md px-2.5 py-1 text-xs font-medium ${vista === v
                      ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-950 dark:text-white' : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'}`}>
                    {texto}
                  </button>
                ))}
              </div>
            </div>
            {cargando ? <Skeleton className="m-5 h-64" /> : vacio ? (
              <p className="px-5 py-8 text-center text-sm text-slate-500">
                {vista === 'insignias' ? 'Aún nadie tiene insignias.' : 'Nadie ha ganado experiencia en este periodo.'}
              </p>
            ) : (
              <ol className="divide-y divide-slate-200 dark:divide-slate-800">
                {vista === 'insignias'
                  ? porInsignias!.map((p) => (
                    <li key={p.usuario_id} className={`flex items-center gap-3 px-5 py-3 ${p.usuario_id === usuario?.id ? 'bg-brand-50/60 dark:bg-brand-500/5' : ''}`}>
                      <Puesto posicion={p.posicion} />
                      <div className="min-w-0 flex-1">
                        <Link to={`/personas/${p.usuario_id}`} className="font-medium text-slate-900 hover:underline dark:text-white">{p.nombre}</Link>
                        {p.usuario_id === usuario?.id && <span className="ml-1 text-xs text-slate-400">(tú)</span>}
                        <p className="truncate text-xs text-slate-500 dark:text-slate-400">{p.rol_nombre}{p.programa && ` · ${p.programa}`}</p>
                        <div className="mt-1"><FilaInsignias insignias={p.insignias} max={8} /></div>
                      </div>
                      <span className="text-right">
                        <span className="block text-lg font-semibold text-slate-900 tabular-nums dark:text-white">{p.total}</span>
                        <span className="text-[11px] text-slate-500">insignias</span>
                      </span>
                    </li>
                  ))
                  : porXP!.map((p) => (
                    <li key={p.usuario_id} className={`flex items-center gap-3 px-5 py-3 ${p.usuario_id === usuario?.id ? 'bg-brand-50/60 dark:bg-brand-500/5' : ''}`}>
                      <Puesto posicion={p.posicion} />
                      <div className="min-w-0 flex-1">
                        <p className="flex flex-wrap items-center gap-1.5">
                          <Link to={`/personas/${p.usuario_id}`} className="font-medium text-slate-900 hover:underline dark:text-white">{p.nombre}</Link>
                          <NivelChip nivel={p.nivel} xp={p.xp_total} />
                          {p.usuario_id === usuario?.id && <span className="text-xs text-slate-400">(tú)</span>}
                        </p>
                        <p className="truncate text-xs text-slate-500 dark:text-slate-400">{p.rol_nombre}{p.programa && ` · ${p.programa}`}</p>
                      </div>
                      <span className="text-right">
                        <span className="block text-lg font-semibold text-slate-900 tabular-nums dark:text-white">
                          {vista === 'siempre' ? '' : '+'}{p.xp.toLocaleString('es-CO')}
                        </span>
                        <span className="text-[11px] text-slate-500">XP {vista === 'semana' ? 'esta semana' : vista === 'mes' ? 'este mes' : 'en total'}</span>
                      </span>
                    </li>
                  ))}
              </ol>
            )}
          </section>
        )}

        <section className="card">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 className="font-semibold text-slate-900 dark:text-white">Cómo obtener cada insignia</h2>
            <select className="input w-auto py-1 text-xs" value={tipo} onChange={(e) => setTipo(e.target.value as TipoInsignia | 'todas')} aria-label="Tipo">
              <option value="todas">Todas</option>
              {(Object.keys(TIPO_LABEL) as TipoInsignia[]).map((t) => <option key={t} value={t}>{TIPO_LABEL[t]}</option>)}
            </select>
          </div>
          {!insignias ? <Skeleton className="m-5 h-64" /> : (
            <ul className="divide-y divide-slate-200 dark:divide-slate-800">
              {insignias.filter((i: Insignia) => tipo === 'todas' || i.tipo === tipo).map((i) => (
                <li key={i.id} className="flex items-start gap-3 px-5 py-3">
                  <Medalla icono={i.icono} color={i.color} tipo={i.tipo} />
                  <div className="min-w-0 flex-1">
                    <p className="flex flex-wrap items-center gap-1.5 text-sm font-medium text-slate-900 dark:text-white">
                      {i.nombre} <span className={`rounded-full px-1.5 py-px text-[10px] font-medium ${TIPO_CLASE[i.tipo]}`}>{TIPO_LABEL[i.tipo]}</span>
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{i.descripcion}{i.entidad && ` · En nombre de ${i.entidad}`}</p>
                    <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">{i.texto_regla} · {i.otorgadas} {i.otorgadas === 1 ? 'persona la tiene' : 'personas la tienen'}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
