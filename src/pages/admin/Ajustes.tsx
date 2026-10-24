import { useEffect, useState } from 'react'
import { Mail, Send, X } from 'lucide-react'
import { enviarResumenes, guardarAjustes, leerAjustes } from '@/lib/admin'
import type { Ajustes } from '@/lib/types'
import { Skeleton } from '@/components/ui'
import { Aviso, BotonGuardar, Interruptor, Tarjeta, useCarga } from './comun'

const CORREOS: { clave: keyof Ajustes; titulo: string; detalle: string }[] = [
  { clave: 'correo_solicitudes', titulo: 'Solicitudes e invitaciones nuevas', detalle: 'A quien debe responderlas, con la propuesta completa.' },
  { clave: 'correo_respuestas', titulo: 'Respuestas con motivo', detalle: 'Aprobada, rechazada o retirada, con el motivo y el comentario.' },
  { clave: 'correo_mensajes', titulo: 'Resumen de mensajes sin leer', detalle: 'Un solo correo por persona con los chats pendientes.' },
  { clave: 'correo_logros', titulo: 'Insignias ganadas', detalle: 'Cuando alguien recibe una insignia, automática o manual.' },
  { clave: 'correo_cuenta', titulo: 'Avisos de cuenta y moderación', detalle: 'Cambio de rol, cuenta desactivada o reactivada, proyecto retirado.' },
]

export function AjustesGenerales() {
  const { datos, error } = useCarga(leerAjustes)
  const [form, setForm] = useState<Ajustes | null>(null)
  const [dominio, setDominio] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'error'; texto: string } | null>(null)

  useEffect(() => {
    if (datos) setForm(datos)
  }, [datos])

  if (error) return <Aviso>{error}</Aviso>
  if (!form) return <Skeleton className="h-96" />

  const agregarDominio = () => {
    const d = dominio.trim().toLowerCase().replace(/^@/, '')
    if (d && !form.dominios_permitidos.includes(d)) setForm({ ...form, dominios_permitidos: [...form.dominios_permitidos, d] })
    setDominio('')
  }

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault()
    setOcupado(true)
    setMensaje(null)
    try {
      setForm(await guardarAjustes(form))
      setMensaje({ tipo: 'ok', texto: 'Ajustes guardados.' })
    } catch (err) {
      setMensaje({ tipo: 'error', texto: (err as Error).message })
    } finally {
      setOcupado(false)
    }
  }

  const resumenAhora = async () => {
    setMensaje(null)
    try {
      const { avisos } = await enviarResumenes()
      setMensaje({ tipo: 'ok', texto: avisos ? `Se enviaron ${avisos} resúmenes de mensajes sin leer.` : 'Nadie tiene mensajes pendientes para avisar ahora.' })
    } catch (err) {
      setMensaje({ tipo: 'error', texto: (err as Error).message })
    }
  }

  return (
    <form onSubmit={guardar} className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <Tarjeta titulo="Registro de cuentas" descripcion="Dominios de correo con los que se pueden registrar estudiantes, docentes y administrativos. Sin dominios, se acepta cualquiera. Los aliados externos no se restringen.">
          <div className="flex gap-2">
            <input className="input" placeholder="dominio.edu.co" value={dominio} onChange={(e) => setDominio(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); agregarDominio() } }} aria-label="Nuevo dominio" />
            <button type="button" className="btn-ghost" onClick={agregarDominio} disabled={!dominio.trim()}>Agregar</button>
          </div>
          <ul className="mt-3 flex flex-wrap gap-2">
            {form.dominios_permitidos.length === 0 && <li className="text-sm text-amber-700 dark:text-amber-400">Cualquier dominio puede registrarse.</li>}
            {form.dominios_permitidos.map((d) => (
              <li key={d} className="inline-flex items-center gap-1 rounded-full bg-slate-100 py-1 pr-1 pl-3 text-sm dark:bg-slate-800">
                @{d}
                <button type="button" className="rounded-full p-0.5 text-slate-500 hover:bg-slate-200 hover:text-rose-600 dark:hover:bg-slate-700"
                  onClick={() => setForm({ ...form, dominios_permitidos: form.dominios_permitidos.filter((x) => x !== d) })} aria-label={`Quitar ${d}`}>
                  <X size={13} />
                </button>
              </li>
            ))}
          </ul>
        </Tarjeta>

        <Tarjeta titulo="Correos de alerta" descripcion="Interruptores generales. Además, cada persona puede apagar los suyos (salvo los de cuenta) desde su perfil."
          extra={<Mail size={16} className="text-slate-400" aria-hidden />}>
          <ul className="space-y-3">
            {CORREOS.map((c) => (
              <li key={c.clave} className="flex items-start justify-between gap-4">
                <span className="text-sm">
                  <span className="font-medium text-slate-800 dark:text-slate-200">{c.titulo}</span>
                  <span className="block text-xs text-slate-500 dark:text-slate-400">{c.detalle}</span>
                </span>
                <Interruptor activo={Boolean(form[c.clave])} etiqueta={c.titulo} alCambiar={(v) => setForm({ ...form, [c.clave]: v })} />
              </li>
            ))}
          </ul>
          <div className="mt-4 border-t border-slate-200 pt-4 dark:border-slate-800">
            <label className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-slate-700 dark:text-slate-300">Avisar de mensajes sin leer después de</span>
              <input type="number" className="input w-24 py-1 tabular-nums" min={5} max={1440} value={form.resumen_espera_minutos}
                onChange={(e) => setForm({ ...form, resumen_espera_minutos: Number(e.target.value) })} />
              <span className="text-slate-700 dark:text-slate-300">minutos</span>
            </label>
            <button type="button" className="btn-ghost mt-3 text-xs" onClick={resumenAhora}>
              <Send size={13} aria-hidden /> Enviar el resumen ahora
            </button>
          </div>
        </Tarjeta>
      </div>
      {mensaje && <Aviso tipo={mensaje.tipo}>{mensaje.texto}</Aviso>}
      <div className="flex justify-end"><BotonGuardar ocupado={ocupado}>Guardar ajustes</BotonGuardar></div>
    </form>
  )
}
