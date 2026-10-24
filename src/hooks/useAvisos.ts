import { useEffect, useState } from 'react'
import { apiHabilitada } from '@/lib/http'
import { contarAvisos, EVENTO_AVISOS } from '@/lib/notificaciones'
import { useSesion } from '@/lib/sesion'

const INTERVALO_MS = 30_000

/** Cuántos avisos sin leer tiene la campana. Se actualiza cada 30 s y al leer avisos. */
export function useAvisosSinLeer(): number {
  const { usuario } = useSesion()
  const [n, setN] = useState(0)

  useEffect(() => {
    if (!apiHabilitada || !usuario) {
      setN(0)
      return
    }
    const cargar = () => {
      if (document.visibilityState === 'hidden') return
      contarAvisos().then((r) => setN(r.no_leidas)).catch(() => {})
    }
    cargar()
    const id = window.setInterval(cargar, INTERVALO_MS)
    window.addEventListener(EVENTO_AVISOS, cargar)
    document.addEventListener('visibilitychange', cargar)
    return () => {
      window.clearInterval(id)
      window.removeEventListener(EVENTO_AVISOS, cargar)
      document.removeEventListener('visibilitychange', cargar)
    }
  }, [usuario])

  return n
}
