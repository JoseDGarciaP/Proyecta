import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { LayoutPublico } from '@/components/LayoutPublico'
import { Dashboard } from '@/pages/Dashboard'
import { Proyectos } from '@/pages/Proyectos'
import { ProyectoDetalle } from '@/pages/ProyectoDetalle'
import { NuevoProyecto } from '@/pages/NuevoProyecto'
import { Actores } from '@/pages/Actores'
import { Oportunidades } from '@/pages/Oportunidades'
import { NoEncontrado } from '@/pages/NoEncontrado'
import { Ingresar } from '@/pages/Ingresar'
import { Registro } from '@/pages/Registro'
import { Perfil } from '@/pages/Perfil'
import { Bienvenida } from '@/pages/Bienvenida'
import { Verificar } from '@/pages/Verificar'
import { RequiereSesion } from '@/components/RequiereSesion'
import { useSesion } from '@/lib/sesion'
import type { ReactNode } from 'react'

/** Con sesión iniciada no tiene sentido ver la bienvenida ni el ingreso: se va al panel. */
function SoloVisitantes({ children }: { children: ReactNode }) {
  const { usuario } = useSesion()
  return usuario ? <Navigate to="/" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route element={<LayoutPublico />}>
        <Route path="bienvenida" element={<SoloVisitantes><Bienvenida /></SoloVisitantes>} />
        <Route path="ingresar" element={<SoloVisitantes><Ingresar /></SoloVisitantes>} />
        <Route path="registro" element={<SoloVisitantes><Registro /></SoloVisitantes>} />
        <Route path="verificar" element={<Verificar />} />
      </Route>
      {/* Todo lo demás es solo para usuarios registrados (en modo demostración queda abierto). */}
      <Route element={<RequiereSesion><Layout /></RequiereSesion>}>
        <Route index element={<Dashboard />} />
        <Route path="proyectos" element={<Proyectos />} />
        <Route path="proyectos/nuevo" element={<NuevoProyecto />} />
        <Route path="proyectos/:id" element={<ProyectoDetalle />} />
        <Route path="actores" element={<Actores />} />
        <Route path="oportunidades" element={<Oportunidades />} />
        <Route path="perfil" element={<Perfil />} />
        <Route path="*" element={<NoEncontrado />} />
      </Route>
    </Routes>
  )
}
