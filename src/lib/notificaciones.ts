import { pedir } from './http'
import type { Notificacion, PreferenciasCorreo } from './types'

/** Se emite al leer avisos, para que la campana se actualice sin esperar. */
export const EVENTO_AVISOS = 'proyecta:avisos'
const avisar = () => window.dispatchEvent(new Event(EVENTO_AVISOS))

export const listarAvisos = (soloNoLeidas = false, limite = 30, offset = 0) =>
  pedir<Notificacion[]>(`/notificaciones?${new URLSearchParams({ solo_no_leidas: String(soloNoLeidas), limite: String(limite), offset: String(offset) })}`)

export const contarAvisos = () => pedir<{ no_leidas: number }>('/notificaciones/conteo')

export const marcarAviso = (id: string) => pedir<Notificacion>(`/notificaciones/${id}/leida`, { method: 'POST' }).finally(avisar)

export const marcarTodos = () => pedir<void>('/notificaciones/leidas', { method: 'POST' }).finally(avisar)

export const eliminarAviso = (id: string) => pedir<void>(`/notificaciones/${id}`, { method: 'DELETE' }).finally(avisar)

export const leerPreferencias = () => pedir<PreferenciasCorreo>('/notificaciones/preferencias')

export const guardarPreferencias = (p: PreferenciasCorreo) =>
  pedir<PreferenciasCorreo>('/notificaciones/preferencias', { method: 'PUT', json: p })
