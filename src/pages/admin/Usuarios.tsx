import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Award, ChevronLeft, ChevronRight, KeyRound, Pencil, Search, TrendingUp, UserPlus } from 'lucide-react'
import { crearUsuario, editarUsuario, enviarEnlaceContrasena, listarUsuarios, type FiltroUsuarios } from '@/lib/admin'
import { useSesion } from '@/lib/sesion'
import type { Rol, RolBreve, UsuarioAdmin } from '@/lib/types'
import { formatDate } from '@/lib/format'
import { Badge, Skeleton } from '@/components/ui'
import { Modal } from '@/components/Modal'
import { CampoCorreo } from '@/components/CampoCorreo'
import { esInstitucional, revisarCorreo } from '@/lib/correo'
import { useDominiosPermitidos, useRoles } from '@/lib/parametros'
import { usePuede } from '@/lib/permisos'
import { InsigniasDe, NivelDe } from '@/components/Insignia'
import { OtorgarInsignia } from './Insignias'
import { useConfirmar } from '@/components/Confirmar'
import { Aviso, BotonGuardar, Interruptor, useCarga } from './comun'

const POR_PAGINA = 20

export function Usuarios() {
  const { usuario: yo } = useSesion()
  const [filtro, setFiltro] = useState<FiltroUsuarios>({ q: '', rol: '', estado: '', offset: 0 })
  const [busqueda, setBusqueda] = useState('')
  const { datos, error, recargar, setDatos } = useCarga(() => listarUsuarios({ ...filtro, limite: POR_PAGINA }), [filtro])
  const [editando, setEditando] = useState<UsuarioAdmin | null>(null)
  const [creando, setCreando] = useState(false)
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)
  const { confirmar, ventana } = useConfirmar()
  const dominios = useDominiosPermitidos()
  const roles = useRoles()
  const puede = usePuede()
  const [premiando, setPremiando] = useState<UsuarioAdmin | null>(null)
  const soyAdmin = yo?.rol === 'admin'

  // Buscar al dejar de escribir.
  useEffect(() => {
    const t = window.setTimeout(() => setFiltro((f) => (f.q === busqueda ? f : { ...f, q: busqueda, offset: 0 })), 300)
    return () => window.clearTimeout(t)
  }, [busqueda])

  /** Por qué no se puede dar este rol (texto vacío = sí se puede). Con `email` vacío no se revisa el correo. */
  const bloqueo = (r: RolBreve, email: string) =>
    r.clave === 'admin' && !soyAdmin ? 'solo un Administrador lo asigna'
      : email && r.institucional && !esInstitucional(email, dominios) ? 'requiere correo institucional' : ''

  const reemplazar = (u: UsuarioAdmin) => setDatos((d) => d && { ...d, items: d.items.map((x) => (x.id === u.id ? u : x)) })

  const cambiar = async (u: UsuarioAdmin, cambios: Partial<UsuarioAdmin>, pregunta?: Parameters<typeof confirmar>[0]) => {
    if (pregunta && !(await confirmar(pregunta))) return
    setMensaje(null)
    try {
      reemplazar(await editarUsuario(u.id, cambios))
    } catch (e) {
      setMensaje({ tipo: 'error', texto: (e as Error).message })
    }
  }

  const enlace = async (u: UsuarioAdmin) => {
    setMensaje(null)
    try {
      setMensaje({ tipo: 'ok', texto: (await enviarEnlaceContrasena(u.id)).detalle })
    } catch (e) {
      setMensaje({ tipo: 'error', texto: (e as Error).message })
    }
  }

  const offset = filtro.offset ?? 0
  const total = datos?.total ?? 0

  return (
    <div className="space-y-4">
      {ventana}
      <div className="flex flex-wrap items-end gap-3">
        <label className="relative min-w-56 flex-1">
          <span className="sr-only">Buscar</span>
          <Search size={16} className="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400" aria-hidden />
          <input className="input pl-9" placeholder="Buscar por nombre, correo o programa" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
        </label>
        <select className="input w-auto" value={filtro.rol} onChange={(e) => setFiltro({ ...filtro, rol: e.target.value as Rol, offset: 0 })} aria-label="Rol">
          <option value="">Todos los roles</option>
          {roles.map((r) => <option key={r.clave} value={r.clave}>{r.nombre}</option>)}
        </select>
        <select className="input w-auto" value={filtro.estado} onChange={(e) => setFiltro({ ...filtro, estado: e.target.value as FiltroUsuarios['estado'], offset: 0 })} aria-label="Estado">
          <option value="">Todos los estados</option>
          <option value="activo">Activos</option>
          <option value="sin_verificar">Sin verificar</option>
          <option value="inactivo">Desactivados</option>
        </select>
        <button className="btn-primary" onClick={() => setCreando(true)}><UserPlus size={15} aria-hidden /> Crear usuario</button>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo}>{mensaje.texto}</Aviso>}
      {error && <Aviso>{error}</Aviso>}

      {!datos ? <Skeleton className="h-96" /> : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[760px] text-sm">
            <thead className="border-b border-slate-200 text-left text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Persona</th>
                <th className="px-4 py-3 font-medium">Rol</th>
                <th className="px-4 py-3 font-medium">Proyectos</th>
                <th className="px-4 py-3 font-medium">Correo</th>
                <th className="px-4 py-3 font-medium">Activa</th>
                <th className="px-4 py-3 font-medium"><span className="sr-only">Acciones</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {datos.items.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-slate-500">No hay usuarios con esos filtros.</td></tr>
              )}
              {datos.items.map((u) => {
                const soyYo = u.id === yo?.id
                // Solo un Administrador puede tocar a otro Administrador.
                const protegido = u.rol === 'admin' && !soyAdmin
                return (
                  <tr key={u.id} className={u.activo ? '' : 'opacity-60'}>
                    <td className="px-4 py-3">
                      <p className="flex flex-wrap items-center gap-1.5 font-medium text-slate-900 dark:text-white">
                        {u.nombre} {soyYo && <span className="text-xs font-normal text-slate-400">(tú)</span>}
                        <NivelDe usuarioId={u.id} />
                        <InsigniasDe usuarioId={u.id} />
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{u.email}</p>
                      <p className="text-xs text-slate-400">{u.programa ?? 'Sin programa'} · desde {formatDate(u.creado_en)}</p>
                    </td>
                    <td className="px-4 py-3">
                      <select className="input w-44 py-1.5" value={u.rol} disabled={soyYo || protegido} aria-label={`Rol de ${u.nombre}`}
                        onChange={(e) => {
                          const rol = e.target.value as Rol
                          cambiar(u, { rol }, rol === 'admin' || u.rol === 'admin' ? {
                            titulo: rol === 'admin' ? `¿Dar rol de administrador a ${u.nombre}?` : `¿Quitar el rol de administrador a ${u.nombre}?`,
                            detalle: rol === 'admin' ? 'Podrá gestionar usuarios, catálogos, ajustes y contenido.' : 'Dejará de ver el panel de administración.',
                            aceptar: 'Cambiar rol',
                            peligro: rol !== 'admin',
                          } : undefined)
                        }}>
                        {roles.map((r) => {
                          const motivo = bloqueo(r, u.email)
                          return <option key={r.clave} value={r.clave} disabled={Boolean(motivo)}>{r.nombre}{motivo ? ` (${motivo})` : ''}</option>
                        })}
                      </select>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600 tabular-nums dark:text-slate-300">
                      {u.proyectos} propios · {u.colaboraciones} colabora
                    </td>
                    <td className="px-4 py-3">
                      {u.verificado ? (
                        <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-500/15 dark:text-emerald-300">Verificado{u.con_google && ' · Google'}</Badge>
                      ) : (
                        <button className="text-xs text-amber-700 hover:underline dark:text-amber-400" onClick={() => cambiar(u, { verificado: true }, {
                          titulo: `¿Marcar el correo de ${u.nombre} como verificado?`, detalle: `Podrá ingresar sin confirmar ${u.email}.`, aceptar: 'Marcar verificado',
                        })}>
                          Sin verificar · verificar
                        </button>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Interruptor activo={u.activo} disabled={soyYo || protegido} etiqueta={`Cuenta de ${u.nombre} activa`}
                        alCambiar={(activo) => cambiar(u, { activo }, activo ? undefined : {
                          titulo: `¿Desactivar la cuenta de ${u.nombre}?`,
                          detalle: 'No podrá ingresar hasta que la reactives. Sus proyectos y mensajes se conservan. Le avisaremos por correo.',
                          aceptar: 'Desactivar', peligro: true,
                        })} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        {puede('admin.insignias') && (
                          <button className="rounded p-1.5 text-slate-500 hover:bg-amber-50 hover:text-amber-700 dark:hover:bg-amber-500/10 dark:hover:text-amber-300" title="Otorgar insignia"
                            aria-label={`Otorgar insignia a ${u.nombre}`} disabled={!u.activo} onClick={() => setPremiando(u)}>
                            <Award size={15} aria-hidden />
                          </button>
                        )}
                        {puede('admin.experiencia') && (
                          <Link to={`/admin/niveles?persona=${u.id}`} className="rounded p-1.5 text-slate-500 hover:bg-brand-50 hover:text-brand-700 dark:hover:bg-brand-500/10 dark:hover:text-brand-300"
                            title="Ajustar experiencia" aria-label={`Ajustar experiencia de ${u.nombre}`}>
                            <TrendingUp size={15} aria-hidden />
                          </Link>
                        )}
                        <button className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:opacity-40 dark:hover:bg-slate-800 dark:hover:text-slate-100" title="Editar datos" aria-label={`Editar a ${u.nombre}`} disabled={protegido} onClick={() => setEditando(u)}>
                          <Pencil size={15} aria-hidden />
                        </button>
                        <button className="rounded p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800 disabled:opacity-40 dark:hover:bg-slate-800 dark:hover:text-slate-100" title="Enviar enlace para cambiar la contraseña"
                          aria-label={`Enviar enlace de contraseña a ${u.nombre}`} disabled={!u.activo} onClick={() => enlace(u)}>
                          <KeyRound size={15} aria-hidden />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <footer className="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-xs text-slate-500 dark:border-slate-800 dark:text-slate-400">
            <span className="tabular-nums">{total === 0 ? 'Sin resultados' : `${offset + 1}–${Math.min(offset + POR_PAGINA, total)} de ${total}`}</span>
            <span className="flex gap-1">
              <button className="btn-ghost px-2 py-1" disabled={offset === 0} onClick={() => setFiltro({ ...filtro, offset: Math.max(0, offset - POR_PAGINA) })} aria-label="Anterior"><ChevronLeft size={15} /></button>
              <button className="btn-ghost px-2 py-1" disabled={offset + POR_PAGINA >= total} onClick={() => setFiltro({ ...filtro, offset: offset + POR_PAGINA })} aria-label="Siguiente"><ChevronRight size={15} /></button>
            </span>
          </footer>
        </div>
      )}

      {premiando && <OtorgarInsignia persona={{ id: premiando.id, nombre: premiando.nombre }} alCerrar={() => setPremiando(null)}
        alOtorgar={(texto) => { setPremiando(null); setMensaje({ tipo: 'ok', texto }) }} />}
      {editando && <EditarDatos u={editando} alCerrar={() => setEditando(null)} alGuardar={(u) => { reemplazar(u); setEditando(null) }} />}
      {creando && <CrearUsuario roles={roles} bloqueo={(r) => bloqueo(r, '')} alCerrar={() => setCreando(false)} alCrear={(u) => {
        setCreando(false)
        setMensaje({ tipo: 'ok', texto: `Cuenta creada. Enviamos a ${u.email} un enlace para que elija su contraseña.` })
        void recargar()
      }} />}
    </div>
  )
}

function EditarDatos({ u, alCerrar, alGuardar }: { u: UsuarioAdmin; alCerrar: () => void; alGuardar: (u: UsuarioAdmin) => void }) {
  const [nombre, setNombre] = useState(u.nombre)
  const [programa, setPrograma] = useState(u.programa ?? '')
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const guardar = async (e: React.FormEvent) => {
    e.preventDefault()
    setOcupado(true)
    try {
      alGuardar(await editarUsuario(u.id, { nombre: nombre.trim(), programa: programa.trim() || null }))
    } catch (err) {
      setError((err as Error).message)
      setOcupado(false)
    }
  }
  return (
    <Modal titulo={`Editar a ${u.nombre}`} descripcion={u.email} alCerrar={alCerrar}>
      <form onSubmit={guardar} className="space-y-3">
        <label className="block"><span className="label">Nombre</span>
          <input className="input" required minLength={3} maxLength={150} value={nombre} onChange={(e) => setNombre(e.target.value)} /></label>
        <label className="block"><span className="label">Programa o dependencia</span>
          <input className="input" maxLength={150} value={programa} onChange={(e) => setPrograma(e.target.value)} /></label>
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button><BotonGuardar ocupado={ocupado} /></div>
      </form>
    </Modal>
  )
}

function CrearUsuario({ roles, bloqueo, alCerrar, alCrear }: {
  roles: RolBreve[]; bloqueo: (r: RolBreve) => string; alCerrar: () => void; alCrear: (u: UsuarioAdmin) => void
}) {
  const [form, setForm] = useState({ email: '', nombre: '', rol: 'docente' as Rol, programa: '' })
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const [intento, setIntento] = useState(false)
  const dominios = useDominiosPermitidos()
  const institucional = roles.find((r) => r.clave === form.rol)?.institucional ?? true
  const listaDominios = dominios.map((d) => `@${d}`).join(' o ')
  const crear = async (e: React.FormEvent) => {
    e.preventDefault()
    setIntento(true)
    const revision = revisarCorreo(form.email, { institucional, dominios })
    if (revision.error) return
    setOcupado(true)
    setError('')
    try {
      alCrear(await crearUsuario({ ...form, email: revision.normalizado, nombre: form.nombre.trim(), programa: form.programa.trim() || null }))
    } catch (err) {
      setError((err as Error).message)
      setOcupado(false)
    }
  }
  return (
    <Modal titulo="Crear usuario" descripcion="La cuenta queda verificada y le llega un correo para elegir su contraseña." alCerrar={alCerrar}>
      <form onSubmit={crear} className="space-y-3">
        <label className="block"><span className="label">Rol</span>
          <select className="input" value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value as Rol })}>
            {roles.map((r) => <option key={r.clave} value={r.clave} disabled={Boolean(bloqueo(r))}>{r.nombre}</option>)}
          </select></label>
        <CampoCorreo valor={form.email} alCambiar={(email) => setForm({ ...form, email })} institucional={institucional} dominios={dominios}
          forzarRevision={intento} autoComplete="off"
          ayuda={institucional ? `Debe ser un correo institucional ${listaDominios}.` : 'Aliado externo: puede ser su correo personal o el de su organización.'} />
        <label className="block"><span className="label">Nombre completo</span>
          <input className="input" required minLength={3} value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} /></label>
        <label className="block"><span className="label">{institucional ? 'Programa o dependencia' : 'Organización'}</span>
          <input className="input" value={form.programa} onChange={(e) => setForm({ ...form, programa: e.target.value })} /></label>
        <Aviso>{error}</Aviso>
        <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={alCerrar}>Cancelar</button><BotonGuardar ocupado={ocupado}>Crear y enviar correo</BotonGuardar></div>
      </form>
    </Modal>
  )
}
