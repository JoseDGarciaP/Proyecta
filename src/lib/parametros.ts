import { useEffect, useState } from 'react'
import { apiHabilitada, pedir } from './http'
import { AREAS, ODS, type ItemCatalogo, type ParametrosColaboracion, type RolBreve } from './types'
import { DOMINIO_INSTITUCIONAL } from './correo'

/**
 * Catálogos que configura el admin. Se piden una vez por sesión de la página y se comparten;
 * `invalidarParametros()` los vuelve a pedir (el panel de admin lo llama al guardar).
 */

let colaboracion: Promise<ParametrosColaboracion> | null = null
let areas: Promise<string[]> | null = null
let ods: Promise<ItemCatalogo[]> | null = null
let dominios: Promise<string[]> | null = null
let roles: Promise<RolBreve[]> | null = null
let rolesRegistro: Promise<RolBreve[]> | null = null
const oyentes = new Set<() => void>()

export function invalidarParametros() {
  colaboracion = areas = ods = null
  dominios = null
  roles = rolesRegistro = null
  oyentes.forEach((f) => f())
}

function useCompartido<T>(cargar: () => Promise<T>, inicial: T): T {
  const [valor, setValor] = useState<T>(inicial)
  const [version, setVersion] = useState(0)
  useEffect(() => {
    const f = () => setVersion((v) => v + 1)
    oyentes.add(f)
    return () => {
      oyentes.delete(f)
    }
  }, [])
  useEffect(() => {
    let vigente = true
    cargar().then((v) => vigente && setValor(v)).catch(() => {})
    return () => {
      vigente = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version])
  return valor
}

/** Motivos, tipos de aporte y plantillas activos. `null` mientras cargan. */
export function useParametrosColaboracion(): ParametrosColaboracion | null {
  return useCompartido(() => (colaboracion ??= pedir<ParametrosColaboracion>('/parametros/colaboracion')), null)
}

/** Nombres de las áreas (con la API, las que configuró el admin). */
export function useAreas(): string[] {
  return useCompartido(
    () => (areas ??= apiHabilitada ? pedir<ItemCatalogo[]>('/catalogo/areas').then((xs) => xs.map((a) => a.nombre)) : Promise.resolve([...AREAS])),
    [...AREAS],
  )
}

/** ODS con los nombres que configuró el admin. */
export function useOds(): ItemCatalogo[] {
  return useCompartido(() => (ods ??= apiHabilitada ? pedir<ItemCatalogo[]>('/catalogo/ods') : Promise.resolve(ODS)), ODS)
}

/** Dominios institucionales (Administración → Ajustes). Por defecto @ufpso.edu.co mientras cargan. */
export function useDominiosPermitidos(): string[] {
  return useCompartido(
    () => (dominios ??= apiHabilitada
      ? pedir<{ dominios: string[] }>('/auth/config').then((c) => c.dominios)
      : Promise.resolve([DOMINIO_INSTITUCIONAL])),
    [DOMINIO_INSTITUCIONAL],
  )
}

/** Todos los roles (para filtros y selectores del admin). */
export function useRoles(): RolBreve[] {
  return useCompartido(() => (roles ??= pedir<RolBreve[]>('/roles')), [])
}

/** Roles que se pueden elegir en la página de registro. */
export function useRolesRegistro(): RolBreve[] {
  return useCompartido(() => (rolesRegistro ??= apiHabilitada ? pedir<RolBreve[]>('/auth/roles') : Promise.resolve([])), [])
}
