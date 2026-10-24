import { Fragment, useEffect, useMemo, useState } from 'react'
import { Lock, Pencil, Plus, Save, Trash2 } from 'lucide-react'
import { crearRol, editarRol, eliminarRol, listarPermisos, listarRolesAdmin, type RolEntrada } from '@/lib/admin'
import { invalidarParametros } from '@/lib/parametros'
import type { PermisoDef, RolDef } from '@/lib/types'
import { Badge, Skeleton } from '@/components/ui'
import { Modal } from '@/components/Modal'
import { Aviso, BotonGuardar, Tarjeta, useCarga } from './comun'

/** Matriz de permisos por rol, y crear, editar o eliminar roles. Solo para el rol Administrador. */
export function Roles() {
  const roles = useCarga(listarRolesAdmin)
  const permisos = useCarga(listarPermisos)
  // Cambios sin guardar: clave del rol → permisos marcados.
  const [borrador, setBorrador] = useState<Record<string, Set<string>>>({})
  const [guardando, setGuardando] = useState(false)
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)
  const [editando, setEditando] = useState<RolDef | 'nuevo' | null>(null)
  const [eliminando, setEliminando] = useState<RolDef | null>(null)

  useEffect(() => setBorrador({}), [roles.datos])

  const grupos = useMemo(() => {
    const g = new Map<string, PermisoDef[]>()
    permisos.datos?.forEach((p) => g.set(p.grupo, [...(g.get(p.grupo) ?? []), p]))
    return [...g.entries()]
  }, [permisos.datos])

  if (roles.error || permisos.error) return <Aviso>{roles.error || permisos.error}</Aviso>
  if (!roles.datos || !permisos.datos) return <Skeleton className="h-96" />

  const todosRoles = roles.datos
  const actuales = (r: RolDef) => borrador[r.clave] ?? new Set(r.permisos)
  const cambiados = roles.datos.filter((r) => borrador[r.clave])

  const alternar = (r: RolDef, p: string) => {
    const s = new Set(actuales(r))
    if (!s.delete(p)) s.add(p)
    const igual = s.size === r.permisos.length && r.permisos.every((x) => s.has(x))
    setBorrador((b) => {
      const n = { ...b }
      if (igual) delete n[r.clave]
      else n[r.clave] = s
      return n
    })
  }

  const alternarGrupo = (r: RolDef, lista: PermisoDef[], marcar: boolean) => {
    const s = new Set(actuales(r))
    lista.filter((p) => !p.solo_admin).forEach((p) => (marcar ? s.add(p.clave) : s.delete(p.clave)))
    setBorrador((b) => ({ ...b, [r.clave]: s }))
  }

  const guardar = async () => {
    setGuardando(true)
    setMensaje(null)
    try {
      for (const r of cambiados) {
        await editarRol(r.clave, { nombre: r.nombre, descripcion: r.descripcion, institucional: r.institucional,
          registro_publico: r.registro_publico, permisos: [...borrador[r.clave]] })
      }
      setMensaje({ tipo: 'ok', texto: `Permisos guardados (${cambiados.map((r) => r.nombre).join(', ')}). Se aplican de inmediato.` })
      invalidarParametros()
      await roles.recargar()
    } catch (e) {
      setMensaje({ tipo: 'error', texto: (e as Error).message })
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="space-y-6">
      <Tarjeta
        titulo="Roles"
        descripcion="Los roles del sistema no se eliminan, pero puedes cambiar sus permisos. Crea roles nuevos para casos especiales (p. ej. «Coordinador de semillero»)."
        extra={<button className="btn-ghost text-xs" onClick={() => setEditando('nuevo')}><Plus size={14} aria-hidden /> Nuevo rol</button>}
      >
        <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {roles.datos.map((r) => (
            <li key={r.clave} className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="flex items-center gap-1.5 font-medium text-slate-900 dark:text-white">
                    {r.nombre} {r.clave === 'admin' && <Lock size={13} className="text-slate-400" aria-label="Acceso total" />}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{r.descripcion || 'Sin descripción'}</p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <button className="rounded p-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-100" onClick={() => setEditando(r)} aria-label={`Editar ${r.nombre}`}><Pencil size={14} /></button>
                  {!r.sistema && (
                    <button className="rounded p-1 text-slate-500 hover:text-rose-600" onClick={() => setEliminando(r)} aria-label={`Eliminar ${r.nombre}`}><Trash2 size={14} /></button>
                  )}
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                <Badge className="bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{r.usuarios} {r.usuarios === 1 ? 'persona' : 'personas'}</Badge>
                <Badge className="bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">{r.permisos.length} permisos</Badge>
                {r.sistema && <Badge className="bg-accent-100 text-accent-800 dark:bg-accent-500/15 dark:text-accent-300">del sistema</Badge>}
                {r.registro_publico && <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300">en el registro</Badge>}
                {!r.institucional && <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-500/15 dark:text-amber-300">correo personal</Badge>}
              </div>
            </li>
          ))}
        </ul>
      </Tarjeta>

      <section className="card">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <div>
            <h2 className="font-semibold text-slate-900 dark:text-white">Permisos por rol</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Marca lo que puede hacer cada rol. El Administrador siempre puede todo; «Roles y permisos» no se delega.</p>
          </div>
          <div className="flex items-center gap-2">
            {cambiados.length > 0 && <span className="text-xs text-amber-700 dark:text-amber-400">{cambiados.length} {cambiados.length === 1 ? 'rol con cambios' : 'roles con cambios'}</span>}
            {cambiados.length > 0 && <button className="btn-ghost text-xs" onClick={() => setBorrador({})}>Descartar</button>}
            <button className="btn-primary" disabled={!cambiados.length || guardando} onClick={guardar}><Save size={15} aria-hidden /> Guardar permisos</button>
          </div>
        </header>
        {mensaje && <div className="px-5 pt-4"><Aviso tipo={mensaje.tipo}>{mensaje.texto}</Aviso></div>}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800">
                <th className="sticky left-0 z-10 bg-white px-5 py-3 text-left text-xs font-medium text-slate-500 dark:bg-slate-900">Permiso</th>
                {todosRoles.map((r) => (
                  <th key={r.clave} className={`px-2 py-3 text-center text-xs font-semibold ${borrador[r.clave] ? 'text-amber-700 dark:text-amber-400' : 'text-slate-700 dark:text-slate-200'}`}>
                    {r.nombre}{borrador[r.clave] && ' •'}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {grupos.map(([grupo, lista]) => (
                <Fragment key={grupo}>
                  <tr className="bg-slate-50 dark:bg-slate-800/40">
                    <th className="sticky left-0 z-10 bg-slate-50 px-5 py-2 text-left text-xs font-semibold tracking-wide text-slate-600 uppercase dark:bg-slate-800 dark:text-slate-300">{grupo}</th>
                    {todosRoles.map((r) => {
                      const todos = lista.filter((p) => !p.solo_admin).every((p) => actuales(r).has(p.clave))
                      return (
                        <td key={r.clave} className="px-2 py-2 text-center">
                          {r.clave !== 'admin' && (
                            <button className="text-[11px] text-brand-700 hover:underline dark:text-brand-300" onClick={() => alternarGrupo(r, lista, !todos)}>
                              {todos ? 'ninguno' : 'todos'}
                            </button>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                  {lista.map((p) => (
                    <tr key={p.clave} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/60 dark:border-slate-800/60 dark:hover:bg-slate-800/30">
                      <th className="sticky left-0 z-10 bg-white px-5 py-2 text-left font-normal dark:bg-slate-900">
                        <span className="block text-slate-800 dark:text-slate-200">{p.nombre}</span>
                        <span className="block text-xs text-slate-500 dark:text-slate-400">{p.descripcion}</span>
                      </th>
                      {todosRoles.map((r) => {
                        const fijo = r.clave === 'admin' || p.solo_admin
                        return (
                          <td key={r.clave} className="px-2 py-2 text-center">
                            <input type="checkbox" className="h-4 w-4 accent-brand-600 disabled:opacity-40" checked={r.clave === 'admin' || actuales(r).has(p.clave)}
                              disabled={fijo} onChange={() => alternar(r, p.clave)} aria-label={`${p.nombre} para ${r.nombre}`}
                              title={r.clave === 'admin' ? 'El Administrador siempre tiene todos los permisos' : p.solo_admin ? 'Solo el rol Administrador' : undefined} />
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {editando && (
        <FormRol rol={editando === 'nuevo' ? null : editando} permisos={permisos.datos} alCerrar={() => setEditando(null)}
          alGuardar={() => { setEditando(null); invalidarParametros(); void roles.recargar() }} />
      )}
      {eliminando && (
        <EliminarRol rol={eliminando} otros={roles.datos.filter((r) => r.clave !== eliminando.clave && r.clave !== 'admin')}
          alCerrar={() => setEliminando(null)} alEliminar={() => { setEliminando(null); invalidarParametros(); void roles.recargar() }} />
      )}
    </div>
  )
}

function FormRol({ rol, permisos, alCerrar, alGuardar }: { rol: RolDef | null; permisos: PermisoDef[]; alCerrar: () => void; alGuardar: () => void }) {
  const basicos = ['proyectos.crear', 'colaboracion.solicitar', 'colaboracion.invitar', 'chat.usar', 'usuarios.ver', 'actores.ver', 'oportunidades.ver', 'ia.usar']
  const [f, setF] = useState<RolEntrada>({
    nombre: rol?.nombre ?? '', descripcion: rol?.descripcion ?? '', institucional: rol?.institucional ?? true,
    registro_publico: rol?.registro_publico ?? false, permisos: rol?.permisos ?? basicos.filter((b) => permisos.some((p) => p.clave === b)),
  })
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const esAdmin = rol?.clave === 'admin'
  return (
    <Modal titulo={rol ? `Editar «${rol.nombre}»` : 'Nuevo rol'} descripcion={rol ? undefined : 'Empieza con los permisos básicos; luego ajústalos en la tabla.'} alCerrar={alCerrar}>
      <form className="space-y-3" onSubmit={async (e) => {
        e.preventDefault()
        setOcupado(true)
        try {
          if (rol) await editarRol(rol.clave, f)
          else await crearRol(f)
          alGuardar()
        } catch (err) {
          setError((err as Error).message)
          setOcupado(false)
        }
      }}>
        <label className="block"><span className="label">Nombre</span>
          <input className="input" required minLength={3} maxLength={80} value={f.nombre} onChange={(e) => setF({ ...f, nombre: e.target.value })} placeholder="Coordinador de semillero" /></label>
        <label className="block"><span className="label">Descripción</span>
          <textarea className="input min-h-16" maxLength={500} value={f.descripcion} onChange={(e) => setF({ ...f, descripcion: e.target.value })} /></label>
        {!esAdmin && (
          <>
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5 h-4 w-4 accent-brand-600" checked={f.institucional} onChange={(e) => setF({ ...f, institucional: e.target.checked })} />
              <span>Exige correo institucional<span className="block text-xs text-slate-500">Desmárcalo solo para roles externos, como los aliados.</span></span>
            </label>
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5 h-4 w-4 accent-brand-600" checked={f.registro_publico} onChange={(e) => setF({ ...f, registro_publico: e.target.checked })} />
              <span>Se puede elegir al registrarse<span className="block text-xs text-slate-500">Si no, solo un administrador lo asigna.</span></span>
            </label>
          </>
        )}
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button><BotonGuardar ocupado={ocupado} /></div>
      </form>
    </Modal>
  )
}

function EliminarRol({ rol, otros, alCerrar, alEliminar }: { rol: RolDef; otros: RolDef[]; alCerrar: () => void; alEliminar: () => void }) {
  const [destino, setDestino] = useState(otros[0]?.clave ?? '')
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  return (
    <Modal titulo={`Eliminar el rol «${rol.nombre}»`} alCerrar={alCerrar}>
      <div className="space-y-3">
        {rol.usuarios > 0 ? (
          <label className="block text-sm">
            <span className="label">{rol.usuarios} {rol.usuarios === 1 ? 'persona tiene' : 'personas tienen'} este rol. ¿A qué rol pasan?</span>
            <select className="input" value={destino} onChange={(e) => setDestino(e.target.value)}>
              {otros.map((r) => <option key={r.clave} value={r.clave}>{r.nombre}</option>)}
            </select>
          </label>
        ) : (
          <p className="text-sm text-slate-600 dark:text-slate-300">Nadie tiene este rol. Se eliminará con sus permisos.</p>
        )}
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2">
          <button className="btn-ghost" onClick={alCerrar}>Cancelar</button>
          <button className="btn bg-rose-600 text-white hover:bg-rose-700" disabled={ocupado} onClick={async () => {
            setOcupado(true)
            try {
              await eliminarRol(rol.clave, rol.usuarios ? destino : undefined)
              alEliminar()
            } catch (e) {
              setError((e as Error).message)
              setOcupado(false)
            }
          }}>Eliminar rol</button>
        </div>
      </div>
    </Modal>
  )
}
