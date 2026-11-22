import { useState } from 'react'
import { bitacora } from '@/lib/admin'
import { Skeleton } from '@/components/ui'
import { Aviso, fechaHora, useCarga } from './comun'

const FILTROS = [
  ['', 'Todo'], ['usuario', 'Usuarios'], ['motivos', 'Motivos'], ['tipos-aporte', 'Tipos de aporte'], ['plantillas', 'Plantillas'],
  ['area', 'Áreas'], ['ods', 'ODS'], ['ajustes', 'Ajustes'], ['proyecto', 'Proyectos'], ['oportunidad', 'Oportunidades'], ['actor', 'Actores'],
  ['alianza', 'Alianzas'], ['recomendacion', 'Recomendaciones'], ['aliado', 'Aliados'], ['reporte', 'Reportes'],
] as const

const OBJETO: Record<string, string> = {
  usuario: 'el usuario', motivos: 'el motivo', 'tipos-aporte': 'el tipo de aporte', plantillas: 'la plantilla', area: 'el área',
  ods: 'el', ajustes: 'los', proyecto: 'el proyecto', oportunidad: 'la oportunidad', actor: 'el actor', resumenes: 'el',
}

const VERBO: Record<string, string> = {
  crear: 'creó', editar: 'editó', eliminar: 'eliminó', restablecer: 'envió enlace a', enviar: 'envió', archivar: 'archivó',
  ocultar: 'ocultó', restaurar: 'restauró', anular: 'anuló', aceptar: 'aceptó', transferir: 'transfirió', exportar: 'exportó',
  aprobar: 'aprobó', rechazar: 'rechazó',
}

/** Quién hizo qué en la administración, del más reciente al más antiguo. */
export function Registro() {
  const [accion, setAccion] = useState('')
  const [usuario, setUsuario] = useState('')
  const [buscar, setBuscar] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const { datos, error } = useCarga(() => bitacora(accion, buscar, desde, hasta), [accion, buscar, desde, hasta])
  return (
    <div className="space-y-4">
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); setBuscar(usuario.trim()) }}>
        <label className="text-xs text-slate-500">Persona
          <input className="input mt-1" placeholder="Nombre o correo (Enter)" value={usuario} onChange={(e) => setUsuario(e.target.value)} />
        </label>
        <label className="text-xs text-slate-500">Desde
          <input type="date" className="input mt-1" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </label>
        <label className="text-xs text-slate-500">Hasta
          <input type="date" className="input mt-1" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </label>
        {(buscar || desde || hasta) && (
          <button type="button" className="btn-ghost text-xs" onClick={() => { setUsuario(''); setBuscar(''); setDesde(''); setHasta('') }}>Limpiar</button>
        )}
      </form>
      <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filtrar">
        {FILTROS.map(([v, l]) => (
          <button key={v} onClick={() => setAccion(v)} aria-pressed={accion === v}
            className={`rounded-full px-3 py-1 text-xs font-medium ${accion === v ? 'bg-brand-600 text-white dark:bg-brand-300 dark:text-brand-950' : 'bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'}`}>
            {l}
          </button>
        ))}
      </div>
      <Aviso>{error}</Aviso>
      {!datos ? <Skeleton className="h-96" /> : datos.length === 0 ? (
        <p className="card px-5 py-10 text-center text-sm text-slate-500">Sin acciones registradas.</p>
      ) : (
        <ol className="card divide-y divide-slate-200 dark:divide-slate-800">
          {datos.map((r) => {
            const [objeto, verbo] = r.accion.split('.')
            return (
              <li key={r.id} className="flex flex-wrap gap-x-4 gap-y-1 px-5 py-3 text-sm">
                <time className="w-40 shrink-0 text-xs text-slate-400 tabular-nums">{fechaHora.format(new Date(r.creado_en))}</time>
                <div className="min-w-0 flex-1">
                  <p className="text-slate-800 dark:text-slate-200">
                    <b className="font-medium">{r.admin_nombre}</b> {VERBO[verbo] ?? verbo} <span className="text-slate-500">{OBJETO[objeto] ?? objeto}</span>{' '}
                    <span className="font-medium">{r.objeto}</span>
                  </p>
                  {r.detalle && <p className="text-xs text-slate-500 dark:text-slate-400">{r.detalle}</p>}
                </div>
              </li>
            )
          })}
        </ol>
      )}
    </div>
  )
}
