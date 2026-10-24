const money = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
})

export const formatCOP = (value: number) => money.format(value)

export const formatCompactCOP = (value: number) =>
  new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)

/** Fecha corta. Acepta «2026-10-23» (se toma como fecha local) o una fecha y hora ISO completa. */
export const formatDate = (iso: string | null) =>
  iso ? new Date(iso.length === 10 ? iso + 'T00:00:00' : iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'

export const diasRestantes = (iso: string) =>
  Math.ceil((new Date(iso + 'T00:00:00').getTime() - Date.now()) / 86_400_000)

export const slug = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2)
