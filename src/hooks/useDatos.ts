import { useCallback, useEffect, useState } from 'react'
import { listarActores, listarOportunidades, listarProyectos } from '@/lib/api'
import type { Actor, Oportunidad, Proyecto } from '@/lib/types'

export function useDatos() {
  const [proyectos, setProyectos] = useState<Proyecto[]>([])
  const [actores, setActores] = useState<Actor[]>([])
  const [oportunidades, setOportunidades] = useState<Oportunidad[]>([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const recargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const [p, a, o] = await Promise.all([listarProyectos(), listarActores(), listarOportunidades()])
      setProyectos(p)
      setActores(a)
      setOportunidades(o)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'No fue posible cargar la información.')
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    void recargar()
  }, [recargar])

  return { proyectos, actores, oportunidades, cargando, error, recargar }
}
