import { useEffect, useState } from 'react'
import { apiHabilitada, pedir } from './http'
import type { Insignia, InsigniaBreve, MisLogros, OpcionesInsignia, PerfilPublico, PuestoRanking } from './types'

export const catalogoInsignias = () => pedir<Insignia[]>('/insignias')
export const misLogros = () => pedir<MisLogros>('/insignias/mias')
export const ranking = (limite = 20) => pedir<PuestoRanking[]>(`/insignias/ranking?limite=${limite}`)
export const opcionesInsignia = () => pedir<OpcionesInsignia>('/insignias/opciones')
export const perfilPublico = (id: string) => pedir<PerfilPublico>(`/usuarios/${id}/perfil`)

// Insignias junto a los nombres: se piden en lote y se guardan por persona durante la sesión.
const cache = new Map<string, InsigniaBreve[]>()
let pendientes = new Set<string>()
let temporizador: number | null = null
const oyentes = new Set<() => void>()

function pedirLote() {
  const ids = [...pendientes]
  pendientes = new Set()
  temporizador = null
  if (!ids.length) return
  pedir<Record<string, InsigniaBreve[]>>(`/insignias/de?ids=${ids.join(',')}`)
    .then((r) => ids.forEach((id) => cache.set(id, r[id] ?? [])))
    .catch(() => ids.forEach((id) => cache.set(id, [])))
    .finally(() => oyentes.forEach((f) => f()))
}

/** Insignias vigentes de una persona (vacío mientras cargan). Varias llamadas seguidas van en una sola petición. */
export function useInsigniasDe(usuarioId: string | null | undefined): InsigniaBreve[] {
  const [, setVersion] = useState(0)
  useEffect(() => {
    if (!apiHabilitada || !usuarioId || cache.has(usuarioId)) return
    const f = () => setVersion((v) => v + 1)
    oyentes.add(f)
    pendientes.add(usuarioId)
    temporizador ??= window.setTimeout(pedirLote, 30)
    return () => {
      oyentes.delete(f)
    }
  }, [usuarioId])
  return (usuarioId && cache.get(usuarioId)) || []
}

/** Tras otorgar o retirar, para que se vuelvan a pedir. */
export const olvidarInsignias = (usuarioId?: string) => (usuarioId ? cache.delete(usuarioId) : cache.clear())
