import { apiHabilitada } from './http'
import { useSesion } from './sesion'
import type { Proyecto, Usuario } from './types'

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

/**
 * ¿Puede editar el proyecto? Solo quien lo registró (su líder) o un admin con «proyectos.moderar».
 * Los colaboradores no: así nadie del equipo puede alterar la formulación. La API exige lo mismo.
 */
export function puedeEditarProyecto(usuario: Usuario | null, proyecto: Pick<Proyecto, 'creado_por'> | null): boolean {
  if (!proyecto) return false
  if (!apiHabilitada) return true // modo demostración: sin cuentas
  return Boolean(usuario && (proyecto.creado_por === usuario.id || tiene(usuario, 'proyectos.moderar')))
}

export function usePuedeEditar(proyecto: Pick<Proyecto, 'creado_por'> | null): boolean {
  const { usuario } = useSesion()
  return puedeEditarProyecto(usuario, proyecto)
}
