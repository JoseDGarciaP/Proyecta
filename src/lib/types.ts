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
/** Las áreas las administra el admin: estas son las iniciales (y las del modo demostración). */
export type Area = (typeof AREAS)[number] | (string & {})

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

/** Clave del rol: uno del sistema (estudiante, docente, administrativo, aliado, admin) o uno creado por el admin. */
export type Rol = string

export interface Usuario {
  id: string
  email: string
  nombre: string
  rol: Rol
  rol_nombre: string
  /** Lo que su rol le permite hacer (solo en el usuario propio). */
  permisos?: string[]
  programa: string | null
  bio: string | null
  habilidades: string[]
  intereses: string[]
  verificado?: boolean
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
  pausado: 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300',
}

export type EstadoSolicitud = 'pendiente' | 'aceptada' | 'rechazada' | 'cancelada'

/** Pedido de unión (lo responde quien registró el proyecto) o invitación (la responde el invitado). */
export interface Solicitud {
  id: string
  tipo: 'solicitud' | 'invitacion'
  estado: EstadoSolicitud
  proyecto_id: string
  proyecto_titulo: string
  usuario_id: string
  usuario_nombre: string
  /** Nota adicional opcional. */
  mensaje: string
  /** Formato fijo: lo que ofrece quien pide unirse, o lo que propone el responsable al invitar. */
  tipo_aporte_id: number | null
  rol_propuesto: string
  aporte: string
  habilidades: string[]
  disponibilidad_horas: number | null
  motivacion: string
  /** Decisión: motivo del catálogo y comentario de quien decidió. */
  motivo_id: number | null
  motivo_nombre: string
  respuesta: string
  creado_en: string
  respondida_en: string | null
  /** true si quien consulta es quien debe aceptar o rechazar */
  por_responder: boolean
}

/** Invitación enviada a un correo que aún no tiene cuenta (la ve quien registró el proyecto). */
export interface InvitacionCorreo {
  id: string
  proyecto_id: string
  email: string
  /** «aceptada» = la aceptó desde el enlace y falta que cree la cuenta. */
  estado: EstadoSolicitud
  rol_propuesto: string
  creado_en: string
  expira_en: string
  vencida: boolean
}

/** Resultado de invitar por correo: si el correo ya tenía cuenta se envía una invitación normal. */
export interface ResultadoInvitarCorreo {
  modo: 'usuario' | 'correo'
  solicitud: Solicitud | null
  invitacion: InvitacionCorreo | null
}

/** Lo que ve quien abre el enlace de la invitación (sin sesión). */
export interface InvitacionPublica {
  email: string
  estado: EstadoSolicitud
  vencida: boolean
  proyecto_id: string
  proyecto_titulo: string
  proyecto_resumen: string
  invitado_por: string
  rol_propuesto: string
  aporte: string
  habilidades: string[]
  disponibilidad_horas: number | null
  motivacion: string
  mensaje: string
  cuenta_existe: boolean
  es_miembro: boolean
}

export interface Miembro {
  usuario_id: string
  nombre: string
  programa: string | null
  rol: string
  desde: string
}

export interface Perfil {
  usuario: Usuario
  resumen: { proyectos: number; colaboraciones: number; alianzas_activas: number; por_responder: number }
  proyectos: { proyecto: Proyecto; mi_rol: 'responsable' | 'colaborador' }[]
  alianzas: Solicitud[]
}

/** Resultado de similitud (proyecto, oportunidad o persona) con su explicación. */
export interface Sugerencia {
  id: string
  tipo: 'proyecto' | 'oportunidad' | 'usuario'
  titulo: string
  detalle: string
  similitud: number
  razon: string
}

/** semantico = embeddings con sentence-transformers; lexico = palabras en común (sin modelo). */
export type MetodoSimilitud = 'semantico' | 'lexico'

export interface RespuestaSugerencias {
  metodo: MetodoSimilitud
  resultados: Sugerencia[]
}

export interface SugerenciasParaMi {
  metodo: MetodoSimilitud
  perfil_completo: boolean
  proyectos: Sugerencia[]
  oportunidades: Sugerencia[]
}

/** Mensaje del chat de un proyecto o de la conversación de una solicitud. */
export interface Mensaje {
  id: number
  /** chat del equipo del proyecto */
  proyecto_id: string | null
  /** conversación de una solicitud o invitación */
  solicitud_id: string | null
  autor_id: string | null
  autor_nombre: string
  texto: string
  enviado_en: string
  editado_en: string | null
  eliminado: boolean
  /** cambia al enviarlo, editarlo o eliminarlo */
  modificado_en: string
  /** true si lo escribió quien consulta */
  propio: boolean
}

export interface ResumenChat {
  tipo: 'proyecto' | 'solicitud'
  proyecto_id: string
  proyecto_titulo: string
  solicitud_id: string | null
  /** el proyecto, o «Persona · Proyecto» en una solicitud */
  titulo: string
  no_leidos: number
  ultimo: Mensaje | null
}

// ---- Parámetros de colaboración (los configura el admin) ----------------------------------------

export type TipoMotivo = 'aprobacion' | 'rechazo'

export interface Motivo {
  id: number
  tipo: TipoMotivo
  nombre: string
  descripcion: string
  requiere_comentario: boolean
  activo: boolean
  orden: number
}

export interface TipoAporte {
  id: number
  nombre: string
  descripcion: string
  activo: boolean
  orden: number
}

export type ParaPlantilla = 'solicitante' | 'responsable' | 'todos'

export interface Plantilla {
  id: number
  titulo: string
  texto: string
  para: ParaPlantilla
  activo: boolean
  orden: number
}

export interface ParametrosColaboracion {
  motivos: Motivo[]
  tipos_aporte: TipoAporte[]
  plantillas: Plantilla[]
}

/** Lo que se envía al pedir unirse o invitar. */
export interface Recomendacion {
  tipo_aporte_id: number
  aporte: string
  habilidades: string[]
  disponibilidad_horas: number
  motivacion: string
  mensaje: string
}

// ---- Notificaciones ------------------------------------------------------------------------------

export type TipoNotificacion =
  | 'solicitud_nueva'
  | 'invitacion_nueva'
  | 'solicitud_aceptada'
  | 'solicitud_rechazada'
  | 'solicitud_cancelada'
  | 'mensajes_sin_leer'
  | 'cuenta'
  | 'moderacion'
  | 'insignia'
  | 'nivel'
  | 'evidencia'
  | 'postulacion'
  | 'revision'

export interface Notificacion {
  id: string
  tipo: TipoNotificacion
  titulo: string
  cuerpo: string
  enlace: string
  leida: boolean
  correo_enviado: boolean
  creada_en: string
}

export interface PreferenciasCorreo {
  solicitudes: boolean
  respuestas: boolean
  mensajes: boolean
  logros: boolean
}

// ---- Administración ------------------------------------------------------------------------------

export interface UsuarioAdmin {
  id: string
  email: string
  nombre: string
  rol: Rol
  rol_nombre: string
  programa: string | null
  activo: boolean
  verificado: boolean
  con_google: boolean
  creado_en: string
  proyectos: number
  colaboraciones: number
}

export interface PaginaUsuarios {
  total: number
  items: UsuarioAdmin[]
}

export interface AreaAdmin {
  id: number
  nombre: string
  proyectos: number
  oportunidades: number
}

export interface ItemCatalogo {
  id: number
  nombre: string
}

export interface Ajustes {
  dominios_permitidos: string[]
  correo_solicitudes: boolean
  correo_respuestas: boolean
  correo_mensajes: boolean
  correo_cuenta: boolean
  correo_logros: boolean
  resumen_espera_minutos: number
}

export interface Conteo {
  clave: string
  total: number
}

export interface Estadisticas {
  usuarios_total: number
  usuarios_activos: number
  usuarios_sin_verificar: number
  usuarios_inactivos: number
  usuarios_por_rol: Conteo[]
  proyectos: number
  oportunidades_abiertas: number
  actores: number
  solicitudes_por_estado: Conteo[]
  tasa_aprobacion: number | null
  motivos: { motivo: string; tipo: TipoMotivo; total: number }[]
  aportes: Conteo[]
  correos_30_dias: number
  notificaciones_sin_leer: number
}

export interface ProyectoAdmin {
  id: string
  titulo: string
  area: string
  estado: Estado
  responsable_id: string | null
  responsable_nombre: string | null
  responsable_email: string | null
  miembros: number
  solicitudes_pendientes: number
  creado_en: string
}

export interface RegistroAdmin {
  id: string
  admin_nombre: string
  accion: string
  objeto: string
  detalle: string
  creado_en: string
}

// ---- Roles y permisos --------------------------------------------------------------------------

export interface RolBreve {
  clave: string
  nombre: string
  descripcion: string
  institucional: boolean
}

export interface RolDef extends RolBreve {
  registro_publico: boolean
  sistema: boolean
  permisos: string[]
  orden: number
  usuarios: number
}

export interface PermisoDef {
  clave: string
  grupo: string
  nombre: string
  descripcion: string
  solo_admin: boolean
}

// ---- Insignias -------------------------------------------------------------------------------

export type TipoInsignia = 'logro' | 'condecoracion' | 'reconocimiento'

/** Un requisito de una regla automática. `valor`: área, número de ODS, clave de rol o texto, según el criterio. */
export interface Condicion {
  criterio: string
  umbral: number
  valor: string | null
}

export interface Reglas {
  modo: 'todas' | 'alguna'
  condiciones: Condicion[]
}

export interface Insignia {
  id: number
  nombre: string
  descripcion: string
  tipo: TipoInsignia
  entidad: string
  icono: string
  color: string
  /** null = la otorga la administración */
  reglas: Reglas | null
  vence_en: string | null
  vigencia_dias: number | null
  activo: boolean
  orden: number
  automatica: boolean
  texto_regla: string
  otorgadas: number
}

/** Insignia que tiene una persona. */
export interface InsigniaBreve {
  id: number
  nombre: string
  descripcion: string
  tipo: TipoInsignia
  entidad: string
  icono: string
  color: string
  motivo: string
  automatica: boolean
  otorgada_en: string
  fecha_evento: string | null
  vence_en: string | null
}

export interface MisLogros {
  obtenidas: InsigniaBreve[]
  en_progreso: { insignia: Insignia; modo: 'todas' | 'alguna'; condiciones: { texto: string; actual: number; umbral: number }[]; avance: number }[]
  manuales_disponibles: Insignia[]
  vencidas: InsigniaBreve[]
}

export interface CriterioInsignia {
  clave: string
  nombre: string
  unidad: string
  valor: 'area' | 'ods' | 'rol' | 'texto' | null
  binario: boolean
  grupo: string
}

export interface OpcionesInsignia {
  criterios: CriterioInsignia[]
  iconos: string[]
  colores: string[]
  tipos: Record<TipoInsignia, string>
}

export interface PuestoRanking {
  posicion: number
  usuario_id: string
  nombre: string
  rol_nombre: string
  programa: string | null
  total: number
  insignias: InsigniaBreve[]
}

export interface Otorgada {
  usuario_id: string
  nombre: string
  email: string
  motivo: string
  automatica: boolean
  otorgada_por: string | null
  otorgada_en: string
  fecha_evento: string | null
  vence_en: string | null
  retirada_en: string | null
  estado: 'vigente' | 'vencida' | 'retirada'
}

export interface PerfilPublico {
  usuario: Omit<Usuario, 'email' | 'permisos'>
  xp: number
  nivel: NivelBreve | null
  insignias: InsigniaBreve[]
  proyectos: { proyecto: Proyecto; rol: string }[]
}

// ---- Experiencia y niveles -------------------------------------------------------------------

export interface NivelBreve {
  id: number
  nombre: string
  icono: string
  color: string
  posicion: number
}

export interface Nivel {
  id: number
  nombre: string
  descripcion: string
  icono: string
  color: string
  xp_minima: number
  insignias_minimas: number
  insignias_requeridas: number[]
  posicion: number
  personas: number
}

export type NivelEntrada = Omit<Nivel, 'id' | 'posicion' | 'personas'>

export interface AccionXP {
  clave: string
  nombre: string
  descripcion: string
  puntos: number
  tope_diario: number | null
  activo: boolean
  orden: number
}

export interface MovimientoXP {
  id: string
  accion: string
  accion_nombre: string
  puntos: number
  detalle: string
  otorgado_por: string | null
  creado_en: string
}

export interface MiExperiencia {
  xp: number
  xp_semana: number
  nivel: NivelBreve | null
  siguiente: { nivel: Nivel; xp_faltante: number; insignias_faltantes: number; requeridas_faltantes: string[] } | null
  total_niveles: number
  historial: MovimientoXP[]
  acciones: AccionXP[]
}

export interface ExperienciaBreve {
  xp: number
  nivel: NivelBreve | null
}

export interface PuestoXP {
  posicion: number
  usuario_id: string
  nombre: string
  rol_nombre: string
  programa: string | null
  xp: number
  xp_total: number
  nivel: NivelBreve | null
}

export interface PersonaXP {
  id: string
  nombre: string
  email: string
  rol_nombre: string
  xp: number
  nivel: NivelBreve | null
}

export interface ResumenUsuarioXP {
  usuario_id: string
  nombre: string
  xp: number
  nivel: NivelBreve | null
  historial: MovimientoXP[]
}

// ---- Postulaciones y evidencias ----------------------------------------------------------------

export type EstadoPostulacion = 'enviada' | 'aceptada' | 'no_seleccionada' | 'retirada'

export interface Postulacion {
  id: string
  oportunidad_id: string
  oportunidad_titulo: string
  oportunidad_entidad: string
  oportunidad_cierra_en: string
  proyecto_id: string
  proyecto_titulo: string
  usuario_nombre: string | null
  estado: EstadoPostulacion
  nota: string
  comentario: string
  creado_en: string
  decidida_en: string | null
}

export type TipoEvidencia = 'certificado' | 'constancia' | 'informe' | 'foto' | 'otro'
export type EstadoEvidencia = 'pendiente' | 'aprobada' | 'rechazada'

export interface Evidencia {
  id: string
  usuario_id: string
  usuario_nombre: string
  proyecto_id: string | null
  proyecto_titulo: string | null
  titulo: string
  descripcion: string
  tipo: TipoEvidencia
  archivo_nombre: string
  archivo_tipo: string
  archivo_tamano: number
  estado: EstadoEvidencia
  xp_otorgada: number
  comentario: string
  revisada_por: string | null
  revisada_en: string | null
  creado_en: string
}
