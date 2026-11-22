import { pedir } from './http'

/** Datos que pide el registro de un aliado externo (Ep4-Hu12). */
export interface DatosAliado {
  razon_social: string
  tipo: string
  documento: string
  telefono: string
  sector: string
}

export interface AliadoPropio extends DatosAliado {
  usuario_id: string
  sitio_web: string
  descripcion: string
  documento: string
  estado: 'pendiente' | 'aprobado' | 'rechazado'
  motivo_rechazo: string
}

export interface AliadoPublico {
  usuario_id: string
  nombre: string
  razon_social: string
  tipo: string
  sector: string
  sitio_web: string
  descripcion: string
  intereses: string[]
  proyectos: { id: string; titulo: string; rol: string }[]
}

export interface AliadoAdmin extends AliadoPropio {
  nombre: string
  email: string
  creado_en: string
  revisado_en: string | null
}

export const TIPOS_ALIADO = ['Empresa', 'ONG o fundación', 'Entidad pública', 'Gremio o asociación', 'Persona natural', 'Otro']

export function listarAliados(f: { sector?: string; interes?: string; q?: string } = {}) {
  const p = new URLSearchParams(Object.entries(f).filter(([, v]) => v) as [string, string][])
  return pedir<AliadoPublico[]>(`/aliados${p.size ? `?${p}` : ''}`)
}
export const miPerfilAliado = () => pedir<AliadoPropio | null>('/aliados/yo')
export const guardarPerfilAliado = (datos: Partial<Pick<AliadoPropio, 'telefono' | 'sector' | 'sitio_web' | 'descripcion' | 'razon_social'>>) =>
  pedir<AliadoPropio>('/aliados/yo', { method: 'PUT', json: datos })

export const aliadosAdmin = (estado = '') => pedir<AliadoAdmin[]>(`/admin/aliados${estado ? `?estado=${estado}` : ''}`)
export const aprobarAliado = (id: string) => pedir<AliadoAdmin>(`/admin/aliados/${id}/aprobar`, { method: 'POST' })
export const rechazarAliado = (id: string, motivo: string) =>
  pedir<AliadoAdmin>(`/admin/aliados/${id}/rechazar`, { method: 'POST', json: { motivo } })
export const cambiarDocumentoAliado = (id: string, documento: string) =>
  pedir<AliadoAdmin>(`/admin/aliados/${id}/documento`, { method: 'PUT', json: { documento } })
