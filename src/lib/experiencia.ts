import { useEffect, useState } from 'react'
import { apiHabilitada, pedir } from './http'
import type {
  AccionXP, Evidencia, EstadoEvidencia, EstadoPostulacion, ExperienciaBreve, MiExperiencia, Nivel, NivelEntrada,
  PersonaXP, Postulacion, PuestoXP, ResumenUsuarioXP, TipoEvidencia,
} from './types'

// ---- Experiencia y niveles ----
export const miExperiencia = () => pedir<MiExperiencia>('/experiencia/mia')
export const listarNiveles = () => pedir<Nivel[]>('/experiencia/niveles')
export const listarAcciones = () => pedir<AccionXP[]>('/experiencia/acciones')
export const rankingXP = (periodo: 'semana' | 'mes' | 'siempre', limite = 25) =>
  pedir<PuestoXP[]>(`/experiencia/ranking?periodo=${periodo}&limite=${limite}`)

export const adminXP = {
  acciones: () => pedir<AccionXP[]>('/admin/experiencia/acciones'),
  editarAccion: (clave: string, a: Omit<AccionXP, 'clave' | 'orden'>) => pedir<AccionXP>(`/admin/experiencia/acciones/${clave}`, { method: 'PUT', json: a }),
  crearNivel: (n: NivelEntrada) => pedir<Nivel>('/admin/experiencia/niveles', { method: 'POST', json: n }),
  editarNivel: (id: number, n: NivelEntrada) => pedir<Nivel>(`/admin/experiencia/niveles/${id}`, { method: 'PUT', json: n }),
  eliminarNivel: (id: number) => pedir<void>(`/admin/experiencia/niveles/${id}`, { method: 'DELETE' }),
  ajustar: (usuario_id: string, puntos: number, motivo: string) =>
    pedir<ResumenUsuarioXP>('/admin/experiencia/ajustes', { method: 'POST', json: { usuario_id, puntos, motivo } }),
  usuario: (id: string) => pedir<ResumenUsuarioXP>(`/admin/experiencia/usuarios/${id}`),
  personas: (q: string) => pedir<PersonaXP[]>(`/admin/experiencia/personas?q=${encodeURIComponent(q)}`),
  recalcular: () => pedir<{ subieron: number }>('/admin/experiencia/recalcular', { method: 'POST' }),
}

// ---- Postulaciones ----
export const postular = (oportunidadId: string, proyecto_id: string, nota: string) =>
  pedir<Postulacion>(`/oportunidades/${oportunidadId}/postulaciones`, { method: 'POST', json: { proyecto_id, nota } })
export const misPostulaciones = () => pedir<Postulacion[]>('/postulaciones/mias')
export const postulacionesDeProyecto = (proyectoId: string) => pedir<Postulacion[]>(`/proyectos/${proyectoId}/postulaciones`)
export const retirarPostulacion = (id: string) => pedir<Postulacion>(`/postulaciones/${id}/retirar`, { method: 'POST' })
export const adminPostulaciones = {
  listar: (f: { oportunidad_id?: string; estado?: EstadoPostulacion } = {}) =>
    pedir<Postulacion[]>(`/admin/postulaciones?${new URLSearchParams(Object.entries(f).filter(([, v]) => v) as [string, string][])}`),
  decidir: (id: string, estado: Exclude<EstadoPostulacion, 'retirada'>, comentario: string) =>
    pedir<Postulacion>(`/admin/postulaciones/${id}`, { method: 'PATCH', json: { estado, comentario } }),
}

export const ESTADO_POSTULACION: Record<EstadoPostulacion, [string, string]> = {
  enviada: ['En revisión', 'bg-sky-100 text-sky-800 dark:bg-sky-500/15 dark:text-sky-300'],
  aceptada: ['Seleccionado', 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300'],
  no_seleccionada: ['No seleccionado', 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300'],
  retirada: ['Retirada', 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'],
}

// ---- Evidencias ----
export function subirEvidencia(d: { archivo: File; titulo: string; descripcion: string; tipo: TipoEvidencia; proyecto_id?: string }) {
  const f = new FormData()
  f.append('archivo', d.archivo)
  f.append('titulo', d.titulo)
  f.append('descripcion', d.descripcion)
  f.append('tipo', d.tipo)
  if (d.proyecto_id) f.append('proyecto_id', d.proyecto_id)
  return pedir<Evidencia>('/evidencias', { method: 'POST', datos: f })
}
export const misEvidencias = () => pedir<Evidencia[]>('/evidencias/mias')
export const evidenciasDeProyecto = (proyectoId: string) => pedir<Evidencia[]>(`/proyectos/${proyectoId}/evidencias`)
export const eliminarEvidencia = (id: string) => pedir<void>(`/evidencias/${id}`, { method: 'DELETE' })
export const adminEvidencias = {
  listar: (estado?: EstadoEvidencia) => pedir<Evidencia[]>(`/admin/evidencias${estado ? `?estado=${estado}` : ''}`),
  revisar: (id: string, aprobar: boolean, puntos: number | null, comentario: string) =>
    pedir<Evidencia>(`/admin/evidencias/${id}/revisar`, { method: 'POST', json: { aprobar, puntos, comentario } }),
}

export const TIPO_EVIDENCIA: Record<TipoEvidencia, string> = {
  certificado: 'Certificado', constancia: 'Constancia', informe: 'Informe', foto: 'Foto', otro: 'Otro',
}
export const ESTADO_EVIDENCIA: Record<EstadoEvidencia, [string, string]> = {
  pendiente: ['En revisión', 'bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300'],
  aprobada: ['Aprobada', 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300'],
  rechazada: ['Rechazada', 'bg-rose-100 text-rose-800 dark:bg-rose-500/15 dark:text-rose-300'],
}
export const TIPOS_ARCHIVO = 'application/pdf,image/png,image/jpeg,image/webp'

// ---- Nivel junto a los nombres: se pide en lote y se guarda por persona durante la sesión ----
const cache = new Map<string, ExperienciaBreve>()
let pendientes = new Set<string>()
let temporizador: number | null = null
const oyentes = new Set<() => void>()

function pedirLote() {
  const ids = [...pendientes]
  pendientes = new Set()
  temporizador = null
  if (!ids.length) return
  pedir<Record<string, ExperienciaBreve>>(`/experiencia/de?ids=${ids.join(',')}`)
    .then((r) => ids.forEach((id) => cache.set(id, r[id] ?? { xp: 0, nivel: null })))
    .catch(() => ids.forEach((id) => cache.set(id, { xp: 0, nivel: null })))
    .finally(() => oyentes.forEach((f) => f()))
}

/** XP y nivel de una persona (null mientras carga). Varias llamadas seguidas van en una sola petición. */
export function useNivelDe(usuarioId: string | null | undefined): ExperienciaBreve | null {
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
  return (usuarioId && cache.get(usuarioId)) || null
}

/** Tras un ajuste o al subir de nivel, para que se vuelva a pedir. */
export const olvidarNivel = (usuarioId?: string) => (usuarioId ? cache.delete(usuarioId) : cache.clear())

export const formatoXP = (n: number) => `${n.toLocaleString('es-CO')} XP`
