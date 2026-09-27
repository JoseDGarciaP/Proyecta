export const ESTADOS = ['idea', 'formulacion', 'ejecucion', 'finalizado', 'pausado'] as const
export type Estado = (typeof ESTADOS)[number]

export const AREAS = [
  'Tecnología',
  'Ambiente',
  'Salud',
  'Educación',
  'Agroindustria',
  'Social',
  'Energía',
] as const
export type Area = (typeof AREAS)[number]

export const TIPOS_ACTOR = ['universidad', 'empresa', 'estado', 'comunidad', 'ong'] as const
export type TipoActor = (typeof TIPOS_ACTOR)[number]

export interface Proyecto {
  id: string
  titulo: string
  resumen: string
  descripcion: string
  area: Area
  estado: Estado
  avance: number
  presupuesto: number
  lider: string
  equipo: string[]
  etiquetas: string[]
  fecha_inicio: string
  fecha_fin: string | null
  actores: string[]
  creado_en: string
  /** Campos que llegan desde la API; los datos de ejemplo pueden no tenerlos. */
  necesidades?: string
  ods?: number[]
  creado_por?: string | null
}

/** Lo que se envía al registrar un proyecto; `lider` vacío = nombre de quien registra. */
export type NuevoProyecto = Omit<Proyecto, 'id' | 'creado_en' | 'creado_por'>

export interface Actor {
  id: string
  nombre: string
  tipo: TipoActor
  sector: string
  contacto: string
  proyectos: number
}

export interface Oportunidad {
  id: string
  titulo: string
  entidad: string
  tipo: 'convocatoria' | 'financiacion' | 'mentoria' | 'infraestructura'
  monto: number | null
  cierra_en: string
  areas: Area[]
  url: string
  descripcion?: string
  ods?: number[]
}

export const ROLES = ['estudiante', 'docente', 'administrativo', 'aliado', 'admin'] as const
export type Rol = (typeof ROLES)[number]

export interface Usuario {
  id: string
  email: string
  nombre: string
  rol: Rol
  programa: string | null
  bio: string | null
  habilidades: string[]
  intereses: string[]
}

/** Objetivos de Desarrollo Sostenible (el número es el id que usa la API). */
export const ODS: { id: number; nombre: string }[] = [
  { id: 1, nombre: 'Fin de la pobreza' },
  { id: 2, nombre: 'Hambre cero' },
  { id: 3, nombre: 'Salud y bienestar' },
  { id: 4, nombre: 'Educación de calidad' },
  { id: 5, nombre: 'Igualdad de género' },
  { id: 6, nombre: 'Agua limpia y saneamiento' },
  { id: 7, nombre: 'Energía asequible y no contaminante' },
  { id: 8, nombre: 'Trabajo decente y crecimiento económico' },
  { id: 9, nombre: 'Industria, innovación e infraestructura' },
  { id: 10, nombre: 'Reducción de las desigualdades' },
  { id: 11, nombre: 'Ciudades y comunidades sostenibles' },
  { id: 12, nombre: 'Producción y consumo responsables' },
  { id: 13, nombre: 'Acción por el clima' },
  { id: 14, nombre: 'Vida submarina' },
  { id: 15, nombre: 'Vida de ecosistemas terrestres' },
  { id: 16, nombre: 'Paz, justicia e instituciones sólidas' },
  { id: 17, nombre: 'Alianzas para lograr los objetivos' },
]

export interface Metricas {
  total: number
  enEjecucion: number
  actores: number
  presupuesto: number
  avancePromedio: number
  porEstado: { estado: Estado; total: number }[]
  porArea: { area: string; total: number }[]
  porMes: { mes: string; nuevos: number; finalizados: number }[]
}

export const ESTADO_LABEL: Record<Estado, string> = {
  idea: 'Idea',
  formulacion: 'En formulación',
  ejecucion: 'En ejecución',
  finalizado: 'Finalizado',
  pausado: 'Pausado',
}

export const ESTADO_CLASS: Record<Estado, string> = {
  idea: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  formulacion: 'bg-accent-100 text-accent-800 dark:bg-accent-500/15 dark:text-accent-300',
  ejecucion: 'bg-brand-100 text-brand-800 dark:bg-brand-500/15 dark:text-brand-300',
  finalizado: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300',
  pausado: 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300',
}
