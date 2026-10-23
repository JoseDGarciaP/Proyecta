import type { Estado } from './types'

/**
 * Paleta de visualización: ocho tonos categóricos en orden fijo (nunca ciclado),
 * con pasos propios para modo claro y oscuro. Validada para daltonismo.
 */
export const SERIES_LIGHT = [
  '#2a78d6',
  '#eb6834',
  '#1baf7a',
  '#eda100',
  '#e87ba4',
  '#008300',
  '#4a3aa7',
  '#e34948',
] as const

export const SERIES_DARK = [
  '#3987e5',
  '#d95926',
  '#199e70',
  '#c98500',
  '#d55181',
  '#008300',
  '#9085e9',
  '#e66767',
] as const

/**
 * Pareja de la identidad para gráficas de dos series: granate + azul pizarra.
 * En oscuro se aclaran para mantener contraste >= 3:1 contra la tarjeta.
 */
export const DUO_LIGHT = ['#7b1e2e', '#4a7396'] as const
export const DUO_DARK = ['#e58796', '#93b6d4'] as const

/** Un color fijo por estado, el mismo que usan las etiquetas de estado de la interfaz. */
const ESTADO_LIGHT: Record<Estado, string> = {
  idea: '#9c99a6',
  formulacion: '#4a7396',
  ejecucion: '#7b1e2e',
  finalizado: '#2f7d5b',
  pausado: '#c98500',
}
const ESTADO_DARK: Record<Estado, string> = {
  idea: '#74717e',
  formulacion: '#93b6d4',
  ejecucion: '#e58796',
  finalizado: '#5fbf93',
  pausado: '#e0a93a',
}

export const colorEstado = (estado: Estado, oscuro: boolean) => (oscuro ? ESTADO_DARK : ESTADO_LIGHT)[estado]

export interface ChartTheme {
  series: readonly string[]
  duo: readonly string[]
  grid: string
  axis: string
  surface: string
  border: string
  text: string
}

export function chartTheme(oscuro: boolean): ChartTheme {
  return oscuro
    ? {
        series: SERIES_DARK,
        duo: DUO_DARK,
        grid: '#2c2a32',
        axis: '#9c99a6',
        surface: '#1c1a20',
        border: '#2c2a32',
        text: '#ebeaee',
      }
    : {
        series: SERIES_LIGHT,
        duo: DUO_LIGHT,
        grid: '#dddce2',
        axis: '#5c5a66',
        surface: '#ffffff',
        border: '#dddce2',
        text: '#1c1a20',
      }
}
