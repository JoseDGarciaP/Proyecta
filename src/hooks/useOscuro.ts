import { useOutletContext } from 'react-router-dom'

/** El layout expone el modo actual para que las gráficas usen la paleta correcta. */
export const useOscuro = () => useOutletContext<{ oscuro: boolean }>().oscuro
