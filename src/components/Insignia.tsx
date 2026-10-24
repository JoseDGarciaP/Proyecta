import {
  Anchor, Atom, Award, Brain, BadgeCheck, Bike, BookOpen, BookOpenCheck, Briefcase, Building2, Calculator, CalendarCheck, Camera,
  ChartColumn, Clock, Code, Compass, Cpu, Crown, Dna, Droplets, Dumbbell, Eye, Feather, Flag, FlaskConical, Flame,
  Footprints, Gem, Gift, Glasses, Globe, Goal, GraduationCap, Hammer, HandHeart, Handshake, Heart, Hourglass, Infinity,
  Key, Landmark, Laptop, Leaf, Lightbulb, Map, Medal, Megaphone, MessageSquare, Mic, Microscope, Mountain, Music,
  Palette, PenTool, Puzzle, Recycle, Ribbon, Rocket, Scale, School, Shield, ShieldCheck, Smile, Sparkles, Sprout, Star,
  Stethoscope, Sun, Target, Telescope, ThumbsUp, Tractor, TreePine, Trophy, Users, Wheat, Wind, Wrench, Zap,
  type LucideIcon,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useNivelDe } from '@/lib/experiencia'
import { useInsigniasDe } from '@/lib/insignias'
import { usePuede } from '@/lib/permisos'
import type { InsigniaBreve, NivelBreve, TipoInsignia } from '@/lib/types'

/** Íconos disponibles (deben coincidir con ICONOS en backend/app/modules/insignias/servicio.py), con su nombre para buscarlos. */
export const ICONOS: Record<string, [LucideIcon, string]> = {
  award: [Award, 'premio'], trophy: [Trophy, 'trofeo copa'], medal: [Medal, 'medalla'], star: [Star, 'estrella'],
  crown: [Crown, 'corona'], gem: [Gem, 'gema diamante'], ribbon: [Ribbon, 'cinta lazo'], badge_check: [BadgeCheck, 'verificado'],
  shield: [Shield, 'escudo'], shield_check: [ShieldCheck, 'escudo verificado'], rocket: [Rocket, 'cohete lanzamiento'],
  lightbulb: [Lightbulb, 'bombillo idea'], sparkles: [Sparkles, 'brillo creatividad'], zap: [Zap, 'rayo energía'],
  flame: [Flame, 'llama fuego racha'], target: [Target, 'diana objetivo'], goal: [Goal, 'meta bandera'], flag: [Flag, 'bandera liderazgo'],
  mountain: [Mountain, 'montaña reto'], compass: [Compass, 'brújula exploración'], handshake: [Handshake, 'apretón alianza'],
  users: [Users, 'personas equipo'], heart: [Heart, 'corazón'], hand_heart: [HandHeart, 'voluntariado mano corazón'],
  smile: [Smile, 'sonrisa'], thumbs_up: [ThumbsUp, 'pulgar arriba'], megaphone: [Megaphone, 'megáfono divulgación'],
  message: [MessageSquare, 'mensaje chat'], gift: [Gift, 'regalo'], infinity: [Infinity, 'infinito constancia'],
  graduation: [GraduationCap, 'birrete grado'], school: [School, 'escuela colegio'], book: [BookOpen, 'libro'],
  book_check: [BookOpenCheck, 'libro aprobado'], brain: [Brain, 'cerebro'], microscope: [Microscope, 'microscopio ciencia'],
  flask: [FlaskConical, 'laboratorio química'], atom: [Atom, 'átomo física'], dna: [Dna, 'adn biología'],
  telescope: [Telescope, 'telescopio'], code: [Code, 'código programación'], cpu: [Cpu, 'procesador hardware'],
  laptop: [Laptop, 'portátil'], chart: [ChartColumn, 'gráfica datos'], calculator: [Calculator, 'calculadora'],
  palette: [Palette, 'paleta arte diseño'], pen: [PenTool, 'pluma diseño'], camera: [Camera, 'cámara foto'],
  mic: [Mic, 'micrófono'], music: [Music, 'música'], leaf: [Leaf, 'hoja ambiente'], sprout: [Sprout, 'brote crecimiento'],
  tree: [TreePine, 'árbol'], recycle: [Recycle, 'reciclaje'], droplets: [Droplets, 'agua gotas'], sun: [Sun, 'sol energía solar'],
  wind: [Wind, 'viento'], wheat: [Wheat, 'trigo agro'], tractor: [Tractor, 'tractor campo'], globe: [Globe, 'mundo global'],
  briefcase: [Briefcase, 'maletín empresa'], building: [Building2, 'edificio entidad'], landmark: [Landmark, 'institución'],
  scale: [Scale, 'balanza justicia'], stethoscope: [Stethoscope, 'salud medicina'], hammer: [Hammer, 'martillo construcción'],
  wrench: [Wrench, 'llave herramienta'], puzzle: [Puzzle, 'rompecabezas'], key: [Key, 'llave'], clock: [Clock, 'reloj'],
  calendar_check: [CalendarCheck, 'calendario asistencia'], hourglass: [Hourglass, 'reloj de arena'], map: [Map, 'mapa'],
  anchor: [Anchor, 'ancla'], feather: [Feather, 'pluma escritura'], dumbbell: [Dumbbell, 'pesas deporte'],
  bike: [Bike, 'bicicleta'], footprints: [Footprints, 'huellas'], eye: [Eye, 'ojo visión'], glasses: [Glasses, 'gafas'],
}

/** Fondo y texto de cada color (claro y oscuro). */
export const COLORES: Record<string, string> = {
  brand: 'bg-brand-100 text-brand-700 ring-brand-200 dark:bg-brand-500/15 dark:text-brand-300 dark:ring-brand-500/30',
  accent: 'bg-accent-100 text-accent-700 ring-accent-200 dark:bg-accent-500/15 dark:text-accent-300 dark:ring-accent-500/30',
  amber: 'bg-amber-100 text-amber-700 ring-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:ring-amber-500/30',
  orange: 'bg-orange-100 text-orange-700 ring-orange-200 dark:bg-orange-500/15 dark:text-orange-300 dark:ring-orange-500/30',
  rose: 'bg-rose-100 text-rose-700 ring-rose-200 dark:bg-rose-500/15 dark:text-rose-300 dark:ring-rose-500/30',
  fuchsia: 'bg-fuchsia-100 text-fuchsia-700 ring-fuchsia-200 dark:bg-fuchsia-500/15 dark:text-fuchsia-300 dark:ring-fuchsia-500/30',
  violet: 'bg-violet-100 text-violet-700 ring-violet-200 dark:bg-violet-500/15 dark:text-violet-300 dark:ring-violet-500/30',
  indigo: 'bg-indigo-100 text-indigo-700 ring-indigo-200 dark:bg-indigo-500/15 dark:text-indigo-300 dark:ring-indigo-500/30',
  sky: 'bg-sky-100 text-sky-700 ring-sky-200 dark:bg-sky-500/15 dark:text-sky-300 dark:ring-sky-500/30',
  teal: 'bg-teal-100 text-teal-700 ring-teal-200 dark:bg-teal-500/15 dark:text-teal-300 dark:ring-teal-500/30',
  emerald: 'bg-emerald-100 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:ring-emerald-500/30',
  lime: 'bg-lime-100 text-lime-700 ring-lime-200 dark:bg-lime-500/15 dark:text-lime-300 dark:ring-lime-500/30',
  slate: 'bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700',
}

export const TIPO_LABEL: Record<TipoInsignia, string> = { logro: 'Logro', condecoracion: 'Condecoración', reconocimiento: 'Reconocimiento' }
export const TIPO_CLASE: Record<TipoInsignia, string> = {
  logro: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  condecoracion: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
  reconocimiento: 'bg-accent-100 text-accent-800 dark:bg-accent-500/15 dark:text-accent-300',
}

/**
 * Círculo con el ícono. La forma cambia según el tipo: el logro es un círculo simple,
 * la condecoración lleva doble aro dorado y el reconocimiento un aro punteado.
 */
export function Medalla({ icono, color, tipo = 'logro', tamano = 'md', apagada = false, titulo }: {
  icono: string; color: string; tipo?: TipoInsignia; tamano?: 'sm' | 'md' | 'lg'; apagada?: boolean; titulo?: string
}) {
  const Icono = ICONOS[icono]?.[0] ?? Award
  const medida = { sm: 'h-5 w-5', md: 'h-9 w-9', lg: 'h-14 w-14' }[tamano]
  const icon = { sm: 11, md: 17, lg: 26 }[tamano]
  const aro = apagada ? '' : tipo === 'condecoracion'
    ? (tamano === 'sm' ? 'outline outline-1 outline-offset-1 outline-amber-400' : 'outline outline-2 outline-offset-2 outline-amber-400 dark:outline-amber-300')
    : tipo === 'reconocimiento' ? (tamano === 'sm' ? '' : 'outline outline-1 outline-offset-2 outline-dashed outline-current') : ''
  return (
    <span title={titulo} className={`relative inline-grid shrink-0 place-items-center rounded-full ring-1 ${medida} ${aro} ${
      apagada ? 'bg-slate-100 text-slate-400 ring-slate-200 grayscale dark:bg-slate-800 dark:text-slate-500 dark:ring-slate-700' : COLORES[color] ?? COLORES.amber}`}>
      <Icono size={icon} aria-hidden />
    </span>
  )
}

/** Fila compacta de insignias (máximo `max`, el resto como «+N»). */
export function FilaInsignias({ insignias, max = 4 }: { insignias: InsigniaBreve[]; max?: number }) {
  if (!insignias.length) return null
  const resto = insignias.length - max
  return (
    <span className="inline-flex items-center gap-1 align-middle" aria-label={`${insignias.length} insignias: ${insignias.map((i) => i.nombre).join(', ')}`}>
      {insignias.slice(0, max).map((i) => (
        <Medalla key={i.id} icono={i.icono} color={i.color} tipo={i.tipo} tamano="sm"
          titulo={`${TIPO_LABEL[i.tipo]}: ${i.nombre}${i.motivo ? ` — ${i.motivo}` : ''}`} />
      ))}
      {resto > 0 && <span className="ml-0.5 text-[10px] font-medium text-slate-500 tabular-nums">+{resto}</span>}
    </span>
  )
}

export function InsigniasDe({ usuarioId, max }: { usuarioId: string; max?: number }) {
  return <FilaInsignias insignias={useInsigniasDe(usuarioId)} max={max} />
}

/** Píldora con el ícono y el nombre del nivel. `compacto` muestra solo el ícono y el número de nivel. */
export function NivelChip({ nivel, xp, compacto = false }: { nivel: NivelBreve | null | undefined; xp?: number; compacto?: boolean }) {
  if (!nivel) return null
  const Icono = ICONOS[nivel.icono]?.[0] ?? Star
  const titulo = `Nivel ${nivel.posicion}: ${nivel.nombre}${xp !== undefined ? ` · ${xp.toLocaleString('es-CO')} XP` : ''}`
  return (
    <span title={titulo} aria-label={titulo}
      className={`inline-flex shrink-0 items-center gap-1 rounded-full px-1.5 py-px align-middle text-[10px] font-semibold ring-1 ${COLORES[nivel.color] ?? COLORES.slate}`}>
      <Icono size={10} aria-hidden />
      {compacto ? <span className="tabular-nums">{nivel.posicion}</span> : nivel.nombre}
    </span>
  )
}

export function NivelDe({ usuarioId, compacto }: { usuarioId: string; compacto?: boolean }) {
  const e = useNivelDe(usuarioId)
  return <NivelChip nivel={e?.nivel} xp={e?.xp} compacto={compacto} />
}

export function NombrePersona({ id, nombre, className = '' }: { id: string; nombre: string; className?: string }) {
  const puede = usePuede()
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5">
      {puede('usuarios.ver') ? (
        <Link to={`/personas/${id}`} className={`hover:underline ${className}`}>{nombre}</Link>
      ) : (
        <span className={className}>{nombre}</span>
      )}
      <NivelDe usuarioId={id} />
      <InsigniasDe usuarioId={id} />
    </span>
  )
}

const fecha = (iso: string) => new Date(iso.length === 10 ? `${iso}T12:00:00` : iso).toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' })

/** Tarjeta de una insignia obtenida: tipo, motivo, entidad, fecha del evento y vigencia. */
export function TarjetaInsignia({ i, vencida = false }: { i: InsigniaBreve; vencida?: boolean }) {
  return (
    <div className={`flex gap-3 rounded-lg border p-3 ${i.tipo === 'condecoracion' && !vencida
      ? 'border-amber-300 bg-amber-50/40 dark:border-amber-500/30 dark:bg-amber-500/5' : 'border-slate-200 dark:border-slate-800'} ${vencida ? 'opacity-60' : ''}`}>
      <Medalla icono={i.icono} color={i.color} tipo={i.tipo} apagada={vencida} />
      <div className="min-w-0">
        <p className="flex flex-wrap items-center gap-1.5 text-sm font-semibold text-slate-900 dark:text-white">
          {i.nombre}
          <span className={`rounded-full px-1.5 py-px text-[10px] font-medium ${TIPO_CLASE[i.tipo]}`}>{TIPO_LABEL[i.tipo]}</span>
        </p>
        <p className="text-xs text-slate-600 dark:text-slate-300">{i.motivo || i.descripcion}</p>
        {i.entidad && <p className="text-xs text-slate-500 dark:text-slate-400">En nombre de {i.entidad}</p>}
        <p className="mt-0.5 text-[11px] text-slate-400">
          {i.fecha_evento ? `Evento: ${fecha(i.fecha_evento)} · ` : ''}
          {fecha(i.otorgada_en)}
          {i.automatica ? ' · automática' : ' · otorgada por la administración'}
          {i.vence_en && (vencida ? ` · venció el ${fecha(i.vence_en)}` : ` · vigente hasta ${fecha(i.vence_en)}`)}
        </p>
      </div>
    </div>
  )
}
