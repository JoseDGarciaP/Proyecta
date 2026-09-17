import { useCallback, useEffect, useState } from 'react'

type Tema = 'light' | 'dark'

const LLAVE = 'proyecta:tema'

function temaInicial(): Tema {
  try {
    const guardado = localStorage.getItem(LLAVE)
    if (guardado === 'light' || guardado === 'dark') return guardado
  } catch {
    /* almacenamiento no disponible */
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function useTheme() {
  const [tema, setTema] = useState<Tema>(temaInicial)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', tema === 'dark')
    try {
      localStorage.setItem(LLAVE, tema)
    } catch {
      /* almacenamiento no disponible */
    }
  }, [tema])

  const alternar = useCallback(() => setTema((t) => (t === 'dark' ? 'light' : 'dark')), [])

  return { tema, alternar }
}
