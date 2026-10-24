import { apiHabilitada } from './http'
import { useSesion } from './sesion'
import type { Usuario } from './types'

/** ¿El rol de esta persona tiene el permiso? En modo demostración (sin API) todo está permitido. */
export function tiene(usuario: Usuario | null, permiso: string): boolean {
  if (!apiHabilitada) return true
  return Boolean(usuario?.permisos?.includes(permiso))
}

/** ¿Tiene acceso a alguna sección del panel de administración? */
export const tienePanel = (usuario: Usuario | null) =>
  apiHabilitada && Boolean(usuario?.permisos?.some((p) => p.startsWith('admin.')))

/** `const puede = usePuede(); puede('proyectos.crear')` */
export function usePuede() {
  const { usuario } = useSesion()
  return (permiso: string) => tiene(usuario, permiso)
}
