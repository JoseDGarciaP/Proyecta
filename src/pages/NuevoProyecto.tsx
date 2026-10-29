import { useNavigate } from 'react-router-dom'
import { crearProyecto } from '@/lib/api'
import { datosDe, FormularioProyecto, formularioVacio } from '@/components/FormularioProyecto'

export function NuevoProyecto() {
  const navegar = useNavigate()

  return (
    <FormularioProyecto
      inicial={formularioVacio()}
      titulo="Registrar proyecto"
      descripcion="La información alimenta el panel de métricas y el motor de recomendaciones."
      textoBoton="Guardar proyecto"
      alGuardar={async (form) => {
        const creado = await crearProyecto({ ...datosDe(form), actores: [] })
        navegar(`/proyectos/${creado.id}`)
      }}
      acciones={(reiniciar) => <button type="button" className="btn-ghost" onClick={reiniciar}>Limpiar</button>}
    />
  )
}
