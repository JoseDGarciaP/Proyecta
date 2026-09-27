import { Route, Routes } from 'react-router-dom'
import { Layout } from '@/components/Layout'
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
import { RequiereSesion } from '@/components/RequiereSesion'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="proyectos" element={<Proyectos />} />
        <Route path="proyectos/nuevo" element={<RequiereSesion><NuevoProyecto /></RequiereSesion>} />
        <Route path="proyectos/:id" element={<ProyectoDetalle />} />
        <Route path="actores" element={<Actores />} />
        <Route path="oportunidades" element={<Oportunidades />} />
        <Route path="perfil" element={<RequiereSesion><Perfil /></RequiereSesion>} />
        <Route path="ingresar" element={<Ingresar />} />
        <Route path="registro" element={<Registro />} />
        <Route path="*" element={<NoEncontrado />} />
      </Route>
    </Routes>
  )
}
