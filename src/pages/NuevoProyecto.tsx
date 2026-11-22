import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { crearProyecto } from '@/lib/api'
import { usePuede } from '@/lib/permisos'
import { datosDe, FormularioProyecto, formularioVacio } from '@/components/FormularioProyecto'
import { CargaLote } from '@/components/CargaLote'

export function NuevoProyecto() {
  const navegar = useNavigate()
  const puede = usePuede()
  // La carga por lote crea cuentas: solo quien administra usuarios.
  const lote = puede('admin.usuarios')
  const [modo, setModo] = useState<'uno' | 'lote'>('uno')

  const formulario = (
    <FormularioProyecto
      inicial={formularioVacio()}
      titulo="Registrar proyecto"
      descripcion="La información alimenta el panel de métricas y el motor de recomendaciones."
      textoBoton="Guardar proyecto"
      alGuardar={async (form) => {
        const creado = await crearProyecto(datosDe(form))
        navegar(`/proyectos/${creado.id}`)
      }}
      acciones={(reiniciar) => <button type="button" className="btn-ghost" onClick={reiniciar}>Limpiar</button>}
    />
  )
  if (!lote) return formulario

  return (
    <div className="space-y-6">
      <div className="mx-auto flex max-w-3xl gap-1 rounded-xl bg-slate-100 p-1 dark:bg-slate-900" role="tablist">
        {([['uno', 'Un proyecto'], ['lote', 'Carga por lote']] as const).map(([clave, texto]) => (
          <button
            key={clave}
            type="button"
            role="tab"
            aria-selected={modo === clave}
            onClick={() => setModo(clave)}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition ${
              modo === clave
                ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-800 dark:text-white'
                : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            {texto}
          </button>
        ))}
      </div>
      {modo === 'uno' ? formulario : (
        <div className="mx-auto max-w-3xl space-y-4">
          <header>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Carga de proyectos por lote</h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Registra varios proyectos y crea las cuentas de sus responsables a partir del Excel del formulario.
            </p>
          </header>
          <CargaLote />
        </div>
      )}
    </div>
  )
}
