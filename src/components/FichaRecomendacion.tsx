import type { Solicitud } from '@/lib/types'

/** La propuesta en formato fijo (rol, aporte, horas, habilidades, motivación) y, si ya se decidió, el motivo. */
export function FichaRecomendacion({ solicitud: s, conDecision = true }: { solicitud: Solicitud; conDecision?: boolean }) {
  const esSolicitud = s.tipo === 'solicitud'
  // Solicitudes creadas antes del formato fijo solo traen el mensaje libre.
  const sinFormato = !s.rol_propuesto && !s.aporte
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm dark:border-slate-800 dark:bg-slate-800/40">
      {sinFormato ? (
        s.mensaje ? <p className="text-slate-600 italic dark:text-slate-300">«{s.mensaje}»</p>
          : <p className="text-slate-500">Sin detalle de la propuesta.</p>
      ) : (
        <dl className="grid gap-x-4 gap-y-2 sm:grid-cols-[max-content_1fr]">
          <Fila titulo={esSolicitud ? 'Rol que ofrece' : 'Rol propuesto'}>
            <span className="font-medium text-slate-900 dark:text-white">{s.rol_propuesto || '—'}</span>
            {s.disponibilidad_horas != null && (
              <span className="ml-2 rounded-full bg-white px-2 py-0.5 text-xs text-slate-600 ring-1 ring-slate-200 tabular-nums dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-700">
                {s.disponibilidad_horas} h/semana
              </span>
            )}
          </Fila>
          <Fila titulo={esSolicitud ? 'Aporte' : 'Qué se espera'}>{s.aporte}</Fila>
          {s.habilidades.length > 0 && (
            <Fila titulo="Habilidades">
              <ul className="flex flex-wrap gap-1">
                {s.habilidades.map((h) => (
                  <li key={h} className="rounded-full bg-white px-2 py-0.5 text-xs ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700">{h}</li>
                ))}
              </ul>
            </Fila>
          )}
          <Fila titulo={esSolicitud ? 'Motivación' : 'Por qué la invitan'}>{s.motivacion}</Fila>
          {s.mensaje && <Fila titulo="Nota">{s.mensaje}</Fila>}
        </dl>
      )}
      {conDecision && s.motivo_nombre && (
        <div className={`mt-3 rounded-md border-l-4 px-3 py-2 ${s.estado === 'aceptada'
          ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-500/10' : 'border-rose-500 bg-rose-50 dark:bg-rose-500/10'}`}>
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
            {s.estado === 'aceptada' ? 'Aprobada' : 'Rechazada'} · motivo
          </p>
          <p className="font-medium text-slate-900 dark:text-white">{s.motivo_nombre}</p>
          {s.respuesta && <p className="mt-0.5 text-slate-600 dark:text-slate-300">«{s.respuesta}»</p>}
        </div>
      )}
    </div>
  )
}

function Fila({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <>
      <dt className="text-xs font-medium text-slate-500 sm:pt-0.5 dark:text-slate-400">{titulo}</dt>
      <dd className="text-slate-700 break-words whitespace-pre-wrap dark:text-slate-200">{children}</dd>
    </>
  )
}
