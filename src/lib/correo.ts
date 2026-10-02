/**
 * Revisión rápida del correo en el navegador, antes de llamar a la API.
 * La API repite estas reglas y además consulta el DNS (MX) y la lista de dominios desechables;
 * la prueba definitiva es el enlace de confirmación que llega al buzón.
 */

export const DOMINIO_INSTITUCIONAL = 'ufpso.edu.co'

const DOMINIOS_COMUNES = [
  DOMINIO_INSTITUCIONAL,
  'gmail.com',
  'hotmail.com',
  'outlook.com',
  'outlook.es',
  'hotmail.es',
  'yahoo.com',
  'yahoo.es',
  'icloud.com',
  'live.com',
]

// Dominios reales que se parecen a los comunes y no deben corregirse.
const PARECIDOS_REALES = new Set(['ufps.edu.co', 'mail.com', 'email.com', 'gmx.com', 'gmx.es', 'aol.com', 'mail.ru', 'ymail.com', 'rocketmail.com'])

// Formato práctico: parte local sin espacios, un @ y un dominio con al menos un punto y TLD de 2+ letras.
const FORMATO = /^[^\s@"(),:;<>[\]\\]+@(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$/i

export interface RevisionCorreo {
  normalizado: string
  error?: string
  sugerencia?: string
}

/** Damerau-Levenshtein restringida: «gmial» está a 1 de «gmail». */
function distancia(a: string, b: string): number {
  const d = Array.from({ length: a.length + 1 }, (_, i) => Array.from({ length: b.length + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0)))
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      const costo = a[i - 1] === b[j - 1] ? 0 : 1
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + costo)
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) d[i][j] = Math.min(d[i][j], d[i - 2][j - 2] + 1)
    }
  }
  return d[a.length][b.length]
}

export function sugerirDominio(dominio: string): string | undefined {
  if (DOMINIOS_COMUNES.includes(dominio) || PARECIDOS_REALES.has(dominio)) return undefined
  return DOMINIOS_COMUNES.find((d) => distancia(dominio, d) === 1)
}

export function revisarCorreo(valor: string, opciones: { institucional?: boolean } = {}): RevisionCorreo {
  const normalizado = valor.trim().toLowerCase()
  if (!normalizado) return { normalizado, error: 'Escribe tu correo.' }
  if (!FORMATO.test(normalizado) || normalizado.includes('..')) {
    return { normalizado, error: 'El correo no tiene un formato válido (ejemplo: nombre@ufpso.edu.co).' }
  }
  const [local, dominio] = normalizado.split('@')
  const sugerido = sugerirDominio(dominio)
  if (sugerido) return { normalizado, error: `¿Quisiste decir ${local}@${sugerido}?`, sugerencia: `${local}@${sugerido}` }
  if (opciones.institucional && dominio !== DOMINIO_INSTITUCIONAL) {
    return { normalizado, error: `Usa tu correo institucional @${DOMINIO_INSTITUCIONAL}, o elige «Aliado externo».` }
  }
  return { normalizado }
}
