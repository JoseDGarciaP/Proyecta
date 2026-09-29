import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import { Skeleton } from '@/components/ui'

/**
 * Solo usuarios con sesión: quien entra a la raíz sin cuenta ve la bienvenida; quien abre
 * un enlace directo va a ingresar y vuelve ahí después. En modo demostración deja pasar.
 */
export function RequiereSesion({ children }: { children: ReactNode }) {
  const { usuario, cargando } = useSesion()
  const { pathname, search } = useLocation()
  if (!apiHabilitada) return children
  if (cargando) return <Skeleton className="m-8 h-96" />
  if (!usuario) {
    return pathname === '/'
      ? <Navigate to="/bienvenida" replace />
      : <Navigate to="/ingresar" state={{ desde: pathname + search }} replace />
  }
  return children
}
