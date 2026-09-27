import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { apiHabilitada } from '@/lib/http'
import { useSesion } from '@/lib/sesion'
import { Skeleton } from '@/components/ui'

/** Pide iniciar sesión antes de mostrar la página. En modo demostración deja pasar. */
export function RequiereSesion({ children }: { children: ReactNode }) {
  const { usuario, cargando } = useSesion()
  const { pathname } = useLocation()
  if (!apiHabilitada) return children
  if (cargando) return <Skeleton className="h-96" />
  if (!usuario) return <Navigate to="/ingresar" state={{ desde: pathname }} replace />
  return children
}
