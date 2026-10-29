import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { actualizarProyecto, obtenerProyecto } from '@/lib/api'
import { apiHabilitada } from '@/lib/http'
import { usePuedeEditar } from '@/lib/permisos'
import { useSesion } from '@/lib/sesion'
import type { Proyecto } from '@/lib/types'
import { EmptyState, Skeleton } from '@/components/ui'
import { datosDe, FormularioProyecto, formularioDe } from '@/components/FormularioProyecto'

export function EditarProyecto() {
  const { id = '' } = useParams()
  const navegar = useNavigate()
  const [proyecto, setProyecto] = useState<Proyecto | null>(null)
  const [cargando, setCargando] = useState(true)
  const puedeEditar = usePuedeEditar(proyecto)
  const { usuario } = useSesion()

  useEffect(() => {
    setCargando(true)
    obtenerProyecto(id).then(setProyecto).finally(() => setCargando(false))
  }, [id])

  if (cargando) return <Skeleton className="h-96" />
  if (!proyecto) {
    return (
      <EmptyState
        titulo="Proyecto no encontrado"
        detalle="El registro solicitado no existe o fue eliminado."
        accion={<Link to="/proyectos" className="btn-primary mt-2">Volver al listado</Link>}
      />
    )
  }
  if (!puedeEditar) {
    return (
      <EmptyState
        titulo="Solo el líder puede editar este proyecto"
        detalle="Para proteger la formulación, únicamente quien registró el proyecto puede cambiar sus datos. Si ves algo por corregir, escríbele por el chat del equipo."
        accion={<Link to={`/proyectos/${proyecto.id}`} className="btn-primary mt-2">Volver al proyecto</Link>}
      />
    )
  }

  const ajeno = apiHabilitada && usuario?.id !== proyecto.creado_por

  return (
    <FormularioProyecto
      inicial={formularioDe(proyecto)}
      titulo="Editar proyecto"
      descripcion={ajeno
        ? 'Estás editando un proyecto ajeno con tu permiso de administración.'
        : 'Solo tú, como líder del proyecto, puedes cambiar estos datos. El equipo verá los cambios de inmediato.'}
      textoBoton="Guardar cambios"
      alGuardar={async (form) => {
        await actualizarProyecto(proyecto.id, datosDe(form))
        navegar(`/proyectos/${proyecto.id}`)
      }}
      acciones={() => <Link to={`/proyectos/${proyecto.id}`} className="btn-ghost">Cancelar</Link>}
    />
  )
}
