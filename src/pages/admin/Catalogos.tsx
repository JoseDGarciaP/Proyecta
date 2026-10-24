import { useState } from 'react'
import { Check, Pencil, Plus, Trash2, X } from 'lucide-react'
import { crearArea, eliminarArea, listarAreas, listarOds, renombrarArea, renombrarOds } from '@/lib/admin'
import { invalidarParametros } from '@/lib/parametros'
import { Skeleton } from '@/components/ui'
import { useConfirmar } from '@/components/Confirmar'
import { Aviso, Tarjeta, useCarga } from './comun'

/** Áreas de conocimiento y nombres de los ODS. */
export function Catalogos() {
  const areas = useCarga(listarAreas)
  const ods = useCarga(listarOds)
  const [nueva, setNueva] = useState('')
  const [error, setError] = useState('')
  const { confirmar, ventana } = useConfirmar()

  const correr = async (accion: () => Promise<unknown>, recargar: () => unknown) => {
    setError('')
    try {
      await accion()
      invalidarParametros()
      await recargar()
      return true
    } catch (e) {
      setError((e as Error).message)
      return false
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {ventana}
      <Tarjeta titulo="Áreas de conocimiento" descripcion="Se usan al registrar proyectos y oportunidades, y en los filtros. Un área en uso no se puede eliminar.">
        <Aviso>{error}</Aviso>
        <form className="mb-4 flex gap-2" onSubmit={async (e) => {
          e.preventDefault()
          if (nueva.trim() && await correr(() => crearArea(nueva.trim()), areas.recargar)) setNueva('')
        }}>
          <input className="input" placeholder="Nueva área" value={nueva} onChange={(e) => setNueva(e.target.value)} maxLength={120} aria-label="Nueva área" />
          <button className="btn-primary" disabled={!nueva.trim()}><Plus size={15} aria-hidden /> Agregar</button>
        </form>
        {!areas.datos ? <Skeleton className="h-48" /> : (
          <ul className="divide-y divide-slate-200 dark:divide-slate-800">
            {areas.datos.map((a) => (
              <FilaEditable key={a.id} valor={a.nombre} detalle={`${a.proyectos} proyectos · ${a.oportunidades} oportunidades`}
                alGuardar={(nombre) => correr(() => renombrarArea(a.id, nombre), areas.recargar)}
                alEliminar={a.proyectos || a.oportunidades ? undefined : async () => {
                  if (await confirmar({ titulo: `¿Eliminar el área «${a.nombre}»?`, aceptar: 'Eliminar', peligro: true }))
                    await correr(() => eliminarArea(a.id), areas.recargar)
                }} />
            ))}
          </ul>
        )}
      </Tarjeta>

      <Tarjeta titulo="Objetivos de Desarrollo Sostenible" descripcion="Los 17 ODS son fijos; puedes ajustar cómo se nombran.">
        {!ods.datos ? <Skeleton className="h-96" /> : (
          <ul className="divide-y divide-slate-200 dark:divide-slate-800">
            {ods.datos.map((o) => (
              <FilaEditable key={o.id} prefijo={`${o.id}.`} valor={o.nombre}
                alGuardar={(nombre) => correr(() => renombrarOds(o.id, nombre), ods.recargar)} />
            ))}
          </ul>
        )}
      </Tarjeta>
    </div>
  )
}

function FilaEditable({ valor, detalle, prefijo, alGuardar, alEliminar }: {
  valor: string; detalle?: string; prefijo?: string; alGuardar: (v: string) => Promise<boolean>; alEliminar?: () => void
}) {
  const [editando, setEditando] = useState(false)
  const [texto, setTexto] = useState(valor)
  return (
    <li className="flex items-center gap-3 py-2">
      {prefijo && <span className="w-6 text-right text-xs text-slate-400 tabular-nums">{prefijo}</span>}
      {editando ? (
        <form className="flex flex-1 gap-1" onSubmit={async (e) => {
          e.preventDefault()
          if (texto.trim() && await alGuardar(texto.trim())) setEditando(false)
        }}>
          <input className="input py-1" autoFocus value={texto} onChange={(e) => setTexto(e.target.value)} maxLength={120} aria-label="Nombre" />
          <button className="rounded p-1.5 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-500/10" aria-label="Guardar"><Check size={15} /></button>
          <button type="button" className="rounded p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => { setTexto(valor); setEditando(false) }} aria-label="Cancelar"><X size={15} /></button>
        </form>
      ) : (
        <>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-slate-800 dark:text-slate-200">{valor}</p>
            {detalle && <p className="text-xs text-slate-500 dark:text-slate-400">{detalle}</p>}
          </div>
          <button className="rounded p-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-100" onClick={() => setEditando(true)} aria-label={`Renombrar ${valor}`}><Pencil size={14} /></button>
          {alEliminar !== undefined || detalle ? (
            <button className="rounded p-1 text-slate-500 hover:text-rose-600 disabled:opacity-30 disabled:hover:text-slate-500" disabled={!alEliminar}
              title={alEliminar ? 'Eliminar' : 'En uso: no se puede eliminar'} onClick={alEliminar} aria-label={`Eliminar ${valor}`}><Trash2 size={14} /></button>
          ) : null}
        </>
      )}
    </li>
  )
}
