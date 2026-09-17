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
 * Pareja azul + fucsia para las gráficas de dos series.
 * Validada en ambos modos: separación normal ΔE 27 y para daltonismo ΔE >= 13,
 * y contraste >= 3:1 contra la superficie de la tarjeta.
 */
export const DUO_LIGHT = ['#2a78d6', '#d55181'] as const
export const DUO_DARK = ['#3987e5', '#d55181'] as const

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
        grid: '#1e293b',
        axis: '#94a3b8',
        surface: '#0f172a',
        border: '#1e293b',
        text: '#e2e8f0',
      }
    : {
        series: SERIES_LIGHT,
        duo: DUO_LIGHT,
        grid: '#e2e8f0',
        axis: '#64748b',
        surface: '#ffffff',
        border: '#e2e8f0',
        text: '#0f172a',
      }
}
