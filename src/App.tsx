import { Route, Routes } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Proyectos } from '@/pages/Proyectos'
import { ProyectoDetalle } from '@/pages/ProyectoDetalle'
import { NuevoProyecto } from '@/pages/NuevoProyecto'
import { Actores } from '@/pages/Actores'
import { Oportunidades } from '@/pages/Oportunidades'
import { NoEncontrado } from '@/pages/NoEncontrado'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="proyectos" element={<Proyectos />} />
        <Route path="proyectos/nuevo" element={<NuevoProyecto />} />
        <Route path="proyectos/:id" element={<ProyectoDetalle />} />
        <Route path="actores" element={<Actores />} />
        <Route path="oportunidades" element={<Oportunidades />} />
        <Route path="*" element={<NoEncontrado />} />
      </Route>
    </Routes>
  )
}
