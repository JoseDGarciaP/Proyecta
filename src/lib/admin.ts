import { pedir } from './http'
import type {
  Actor, Ajustes, AreaAdmin, Estadisticas, ItemCatalogo, Motivo, Oportunidad, PaginaUsuarios, Plantilla,
  ProyectoAdmin, RegistroAdmin, Rol, TipoAporte, UsuarioAdmin, RolDef, PermisoDef, Insignia, Otorgada, InsigniaBreve,
} from './types'

/** Llamadas del panel de administración (todas exigen rol admin en la API). */

export const estadisticas = () => pedir<Estadisticas>('/admin/estadisticas')

export interface FiltroUsuarios {
  q?: string
  rol?: Rol
  estado?: '' | 'activo' | 'inactivo' | 'sin_verificar'
  limite?: number
  offset?: number
}

export function listarUsuarios(f: FiltroUsuarios) {
  const params = new URLSearchParams(
    Object.entries(f).filter(([, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)]),
  )
  return pedir<PaginaUsuarios>(`/admin/usuarios?${params}`)
}

export type CambiosUsuario = Partial<Pick<UsuarioAdmin, 'nombre' | 'programa' | 'rol' | 'activo' | 'verificado'>>
export const editarUsuario = (id: string, cambios: CambiosUsuario) =>
  pedir<UsuarioAdmin>(`/admin/usuarios/${id}`, { method: 'PATCH', json: cambios })

export const crearUsuario = (datos: { email: string; nombre: string; rol: Rol; programa: string | null }) =>
  pedir<UsuarioAdmin>('/admin/usuarios', { method: 'POST', json: datos })

export const enviarEnlaceContrasena = (id: string) =>
  pedir<{ detalle: string }>(`/admin/usuarios/${id}/restablecer`, { method: 'POST' })

// Catálogos
export const listarAreas = () => pedir<AreaAdmin[]>('/admin/areas')
export const crearArea = (nombre: string) => pedir<AreaAdmin>('/admin/areas', { method: 'POST', json: { nombre } })
export const renombrarArea = (id: number, nombre: string) => pedir<AreaAdmin>(`/admin/areas/${id}`, { method: 'PUT', json: { nombre } })
export const eliminarArea = (id: number) => pedir<void>(`/admin/areas/${id}`, { method: 'DELETE' })
export const listarOds = () => pedir<ItemCatalogo[]>('/admin/ods')
export const renombrarOds = (id: number, nombre: string) => pedir<ItemCatalogo>(`/admin/ods/${id}`, { method: 'PUT', json: { nombre } })

/** CRUD de los catálogos simples: motivos, tipos de aporte y plantillas. */
function catalogo<T extends { id: number }>(ruta: string) {
  return {
    listar: () => pedir<T[]>(`/admin/${ruta}`),
    crear: (datos: Omit<T, 'id'>) => pedir<T>(`/admin/${ruta}`, { method: 'POST', json: datos }),
    editar: (id: number, datos: Omit<T, 'id'>) => pedir<T>(`/admin/${ruta}/${id}`, { method: 'PUT', json: datos }),
    eliminar: (id: number) => pedir<void>(`/admin/${ruta}/${id}`, { method: 'DELETE' }),
  }
}
export const motivos = catalogo<Motivo>('motivos')
export const tiposAporte = catalogo<TipoAporte>('tipos-aporte')
export const plantillas = catalogo<Plantilla>('plantillas')

// Ajustes
export const leerAjustes = () => pedir<Ajustes>('/admin/ajustes')
export const guardarAjustes = (a: Ajustes) => pedir<Ajustes>('/admin/ajustes', { method: 'PUT', json: a })
export const enviarResumenes = () => pedir<{ avisos: number }>('/admin/resumenes', { method: 'POST' })

// Moderación
export const listarProyectosAdmin = (q = '') => pedir<ProyectoAdmin[]>(`/admin/proyectos${q ? `?q=${encodeURIComponent(q)}` : ''}`)
export const eliminarProyectoAdmin = (id: string, motivo: string) =>
  pedir<void>(`/admin/proyectos/${id}`, { method: 'DELETE', json: { motivo } })

export type OportunidadEntrada = Omit<Oportunidad, 'id'> & { descripcion: string; ods: number[] }
export const crearOportunidad = (o: OportunidadEntrada) => pedir<Oportunidad>('/oportunidades', { method: 'POST', json: o })
export const editarOportunidad = (id: string, o: OportunidadEntrada) => pedir<Oportunidad>(`/oportunidades/${id}`, { method: 'PUT', json: o })
export const eliminarOportunidad = (id: string) => pedir<void>(`/oportunidades/${id}`, { method: 'DELETE' })

export type ActorEntrada = Omit<Actor, 'id' | 'proyectos'>
export const crearActor = (a: ActorEntrada) => pedir<Actor>('/actores', { method: 'POST', json: a })
export const editarActor = (id: string, a: ActorEntrada) => pedir<Actor>(`/actores/${id}`, { method: 'PUT', json: a })
export const eliminarActor = (id: string) => pedir<void>(`/actores/${id}`, { method: 'DELETE' })

// Bitácora
export const bitacora = (accion = '') => pedir<RegistroAdmin[]>(`/admin/registro${accion ? `?accion=${encodeURIComponent(accion)}` : ''}`)

// Roles y permisos (solo el rol Administrador)
export const listarPermisos = () => pedir<PermisoDef[]>('/admin/permisos')
export const listarRolesAdmin = () => pedir<RolDef[]>('/admin/roles')
export type RolEntrada = Pick<RolDef, 'nombre' | 'descripcion' | 'institucional' | 'registro_publico' | 'permisos'>
export const crearRol = (r: RolEntrada) => pedir<RolDef>('/admin/roles', { method: 'POST', json: r })
export const editarRol = (clave: string, r: RolEntrada) => pedir<RolDef>(`/admin/roles/${clave}`, { method: 'PUT', json: r })
export const eliminarRol = (clave: string, reasignarA?: string) =>
  pedir<void>(`/admin/roles/${clave}${reasignarA ? `?reasignar_a=${encodeURIComponent(reasignarA)}` : ''}`, { method: 'DELETE' })

// Insignias
export type InsigniaEntrada = Omit<Insignia, 'id' | 'otorgadas' | 'automatica' | 'texto_regla'>
export const listarInsigniasAdmin = () => pedir<Insignia[]>('/admin/insignias')
export const crearInsignia = (i: InsigniaEntrada) => pedir<Insignia>('/admin/insignias', { method: 'POST', json: i })
export const editarInsignia = (id: number, i: InsigniaEntrada) => pedir<Insignia>(`/admin/insignias/${id}`, { method: 'PUT', json: i })
export const eliminarInsignia = (id: number) => pedir<void>(`/admin/insignias/${id}`, { method: 'DELETE' })
export const otorgadas = (id: number) => pedir<Otorgada[]>(`/admin/insignias/${id}/otorgadas`)
export interface DatosEntrega { motivo: string; fecha_evento: string | null; vence_en: string | null }
export const otorgarInsignia = (id: number, usuarioId: string, d: DatosEntrega) =>
  pedir<InsigniaBreve>(`/admin/insignias/${id}/otorgar`, { method: 'POST', json: { usuario_id: usuarioId, ...d } })
export const otorgarVarios = (id: number, usuarioIds: string[], proyectoId: string | null, d: DatosEntrega) =>
  pedir<{ otorgadas: string[]; ya_tenian: string[] }>(`/admin/insignias/${id}/otorgar-varios`, {
    method: 'POST', json: { usuario_ids: usuarioIds, proyecto_id: proyectoId, ...d },
  })
export const proyectosParaOtorgar = (q: string) =>
  pedir<{ id: string; titulo: string; equipo: number }[]>(`/admin/insignias/proyectos?q=${encodeURIComponent(q)}`)
export const retirarInsignia = (id: number, usuarioId: string) => pedir<void>(`/admin/insignias/${id}/otorgadas/${usuarioId}`, { method: 'DELETE' })
export const evaluarInsignias = () => pedir<{ otorgadas: number }>('/admin/insignias/evaluar', { method: 'POST' })
export const candidatos = (q: string) =>
  pedir<{ id: string; nombre: string; email: string; rol_nombre: string }[]>(`/admin/insignias/candidatos?q=${encodeURIComponent(q)}`)
