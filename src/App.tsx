import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
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
import { Invitacion } from '@/pages/Invitacion'
import { Recuperar } from '@/pages/Recuperar'
import { Restablecer } from '@/pages/Restablecer'
import { RequiereSesion } from '@/components/RequiereSesion'
import { Notificaciones } from '@/pages/Notificaciones'
import { Admin } from '@/pages/Admin'
import { PerfilPersona } from '@/pages/PerfilPersona'
import { Logros } from '@/pages/Logros'
import { tiene, tienePanel } from '@/lib/permisos'
import { useSesion } from '@/lib/sesion'
import type { ReactNode } from 'react'

/** Con sesión iniciada no tiene sentido ver la bienvenida ni el ingreso: se va al panel
 * (o a la página de la que venía, p. ej. el proyecto al que la invitaron). */
function SoloVisitantes({ children }: { children: ReactNode }) {
  const { usuario } = useSesion()
  const desde = (useLocation().state as { desde?: string } | null)?.desde
  return usuario ? <Navigate to={desde?.startsWith('/') ? desde : '/'} replace /> : children
}

/** El panel de administración solo para roles con algún permiso admin.* (la API también lo exige). */
function SoloAdmin({ children }: { children: ReactNode }) {
  const { usuario } = useSesion()
  return tienePanel(usuario) ? children : <Navigate to="/" replace />
}

/** Páginas que exigen un permiso del rol. */
function ConPermiso({ permiso, children }: { permiso: string; children: ReactNode }) {
  const { usuario } = useSesion()
  return tiene(usuario, permiso) ? children : <Navigate to="/" replace />
}

export default function App() {
  return (
    <Routes>
      <Route element={<LayoutPublico />}>
        <Route path="bienvenida" element={<SoloVisitantes><Bienvenida /></SoloVisitantes>} />
        <Route path="ingresar" element={<SoloVisitantes><Ingresar /></SoloVisitantes>} />
        <Route path="registro" element={<SoloVisitantes><Registro /></SoloVisitantes>} />
        <Route path="recuperar" element={<SoloVisitantes><Recuperar /></SoloVisitantes>} />
        <Route path="verificar" element={<Verificar />} />
        <Route path="restablecer" element={<Restablecer />} />
        <Route path="invitacion" element={<Invitacion />} />
      </Route>
      {/* Todo lo demás es solo para usuarios registrados (en modo demostración queda abierto). */}
      <Route element={<RequiereSesion><Layout /></RequiereSesion>}>
        <Route index element={<Dashboard />} />
        <Route path="proyectos" element={<Proyectos />} />
        <Route path="proyectos/nuevo" element={<ConPermiso permiso="proyectos.crear"><NuevoProyecto /></ConPermiso>} />
        <Route path="proyectos/:id" element={<ProyectoDetalle />} />
        <Route path="actores" element={<ConPermiso permiso="actores.ver"><Actores /></ConPermiso>} />
        <Route path="oportunidades" element={<ConPermiso permiso="oportunidades.ver"><Oportunidades /></ConPermiso>} />
        <Route path="logros" element={<Logros />} />
        <Route path="personas/:id" element={<ConPermiso permiso="usuarios.ver"><PerfilPersona /></ConPermiso>} />
        <Route path="perfil" element={<Perfil />} />
        <Route path="notificaciones" element={<Notificaciones />} />
        <Route path="admin" element={<SoloAdmin><Admin /></SoloAdmin>} />
        <Route path="admin/:pestana" element={<SoloAdmin><Admin /></SoloAdmin>} />
        <Route path="*" element={<NoEncontrado />} />
      </Route>
    </Routes>
  )
}
