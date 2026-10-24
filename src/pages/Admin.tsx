import { NavLink, useParams } from 'react-router-dom'
import { Award, BarChart3, FileBadge, FileClock, KeyRound, ListChecks, Settings, ShieldAlert, Tags, TrendingUp, Users } from 'lucide-react'
import { apiHabilitada } from '@/lib/http'
import { usePuede } from '@/lib/permisos'
import { EmptyState } from '@/components/ui'
import { Resumen } from './admin/Resumen'
import { Usuarios } from './admin/Usuarios'
import { Catalogos } from './admin/Catalogos'
import { Colaboracion } from './admin/Colaboracion'
import { AjustesGenerales } from './admin/Ajustes'
import { Moderacion } from './admin/Moderacion'
import { Registro } from './admin/Registro'
import { Roles } from './admin/Roles'
import { Insignias } from './admin/Insignias'
import { NivelesXP } from './admin/NivelesXP'
import { EvidenciasAdmin } from './admin/Evidencias'

// Cada pestaña aparece solo si el rol tiene su permiso.
const PESTANAS = [
  { id: 'resumen', label: 'Resumen', icon: BarChart3, Componente: Resumen, permiso: 'admin.resumen' },
  { id: 'usuarios', label: 'Usuarios', icon: Users, Componente: Usuarios, permiso: 'admin.usuarios' },
  { id: 'roles', label: 'Roles y permisos', icon: KeyRound, Componente: Roles, permiso: 'admin.roles' },
  { id: 'insignias', label: 'Insignias', icon: Award, Componente: Insignias, permiso: 'admin.insignias' },
  { id: 'niveles', label: 'Niveles y XP', icon: TrendingUp, Componente: NivelesXP, permiso: 'admin.experiencia' },
  { id: 'evidencias', label: 'Evidencias', icon: FileBadge, Componente: EvidenciasAdmin, permiso: 'admin.evidencias' },
  { id: 'colaboracion', label: 'Colaboración', icon: ListChecks, Componente: Colaboracion, permiso: 'admin.colaboracion' },
  { id: 'catalogos', label: 'Áreas y ODS', icon: Tags, Componente: Catalogos, permiso: 'admin.catalogos' },
  { id: 'moderacion', label: 'Moderación', icon: ShieldAlert, Componente: Moderacion, permiso: 'admin.moderacion' },
  { id: 'ajustes', label: 'Ajustes', icon: Settings, Componente: AjustesGenerales, permiso: 'admin.ajustes' },
  { id: 'registro', label: 'Bitácora', icon: FileClock, Componente: Registro, permiso: 'admin.bitacora' },
] as const

/** Panel de administración: parametrización de la plataforma y gestión de usuarios. */
export function Admin() {
  const { pestana } = useParams()
  const puede = usePuede()
  const visibles = PESTANAS.filter((p) => puede(p.permiso))
  const actual = visibles.find((p) => p.id === pestana) ?? visibles[0]

  if (apiHabilitada && !actual) {
    return <EmptyState titulo="Sin acceso" detalle="Tu rol no tiene permisos de administración." />
  }
  if (!apiHabilitada) {
    return <EmptyState titulo="La administración necesita la API" detalle="Conecta el backend (VITE_API_URL) e ingresa con una cuenta de administrador." />
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Administración</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Gestiona usuarios, catálogos, motivos, plantillas, correos, niveles, evidencias y contenido de la plataforma.
        </p>
      </header>
      <nav className="-mx-4 overflow-x-auto px-4 lg:mx-0 lg:px-0" aria-label="Secciones de administración">
        <ul className="flex min-w-max gap-1 border-b border-slate-200 dark:border-slate-800">
          {visibles.map(({ id, label, icon: Icono }) => (
            <li key={id}>
              <NavLink
                to={id === visibles[0].id ? '/admin' : `/admin/${id}`}
                end
                className={() =>
                  `-mb-px flex items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium transition ${
                    actual.id === id
                      ? 'border-brand-600 text-brand-800 dark:border-brand-300 dark:text-brand-200'
                      : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'
                  }`
                }
              >
                <Icono size={15} aria-hidden /> {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <actual.Componente />
    </div>
  )
}
