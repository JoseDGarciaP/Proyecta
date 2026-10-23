import { useCallback, useEffect, useState } from 'react'

/** Lo que elige la persona. 'system' sigue la configuración de su equipo. */
export type PreferenciaTema = 'light' | 'dark' | 'system'
/** Lo que realmente se pinta. */
export type Tema = 'light' | 'dark'

const LLAVE = 'proyecta:tema'
const CONSULTA = '(prefers-color-scheme: dark)'
const EVENTO = 'proyecta:tema'

function leerPreferencia(): PreferenciaTema {
  try {
    const guardado = localStorage.getItem(LLAVE)
    if (guardado === 'light' || guardado === 'dark' || guardado === 'system') return guardado
  } catch {
    /* almacenamiento no disponible */
  }
  return 'system'
}

const sistemaOscuro = () => window.matchMedia(CONSULTA).matches

export function useTheme() {
  const [preferencia, setPreferenciaEstado] = useState<PreferenciaTema>(leerPreferencia)
  const [oscuroSistema, setOscuroSistema] = useState(sistemaOscuro)

  // Si el equipo cambia entre claro y oscuro, el modo "Sistema" lo sigue en vivo.
  useEffect(() => {
    const mq = window.matchMedia(CONSULTA)
    const cambio = () => setOscuroSistema(mq.matches)
    mq.addEventListener('change', cambio)
    return () => mq.removeEventListener('change', cambio)
  }, [])

  // Mantiene sincronizados todos los componentes que usan el hook.
  useEffect(() => {
    const sincronizar = () => setPreferenciaEstado(leerPreferencia())
    window.addEventListener(EVENTO, sincronizar)
    return () => window.removeEventListener(EVENTO, sincronizar)
  }, [])

  const tema: Tema = preferencia === 'system' ? (oscuroSistema ? 'dark' : 'light') : preferencia

  useEffect(() => {
    document.documentElement.classList.toggle('dark', tema === 'dark')
  }, [tema])

  const setPreferencia = useCallback((p: PreferenciaTema) => {
    try {
      localStorage.setItem(LLAVE, p)
    } catch {
      /* almacenamiento no disponible */
    }
    setPreferenciaEstado(p)
    window.dispatchEvent(new Event(EVENTO))
  }, [])

  return { tema, preferencia, setPreferencia }
}
