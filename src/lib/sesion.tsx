import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { apiHabilitada, pedir, token } from './http'
import type { Rol, Usuario } from './types'

export interface DatosRegistro {
  nombre: string
  email: string
  password: string
  rol: Rol
  programa: string | null
}

interface Sesion {
  usuario: Usuario | null
  cargando: boolean
  ingresar: (email: string, password: string) => Promise<void>
  registrar: (datos: DatosRegistro) => Promise<void>
  salir: () => void
}

const SesionContext = createContext<Sesion | null>(null)

export function SesionProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [cargando, setCargando] = useState(apiHabilitada && Boolean(token.leer()))

  useEffect(() => {
    if (!apiHabilitada || !token.leer()) return
    pedir<Usuario>('/usuarios/yo')
      .then(setUsuario)
      .catch(() => token.borrar())
      .finally(() => setCargando(false))
  }, [])

  const ingresar = async (email: string, password: string) => {
    const { access_token } = await pedir<{ access_token: string }>('/auth/login', {
      method: 'POST',
      form: { username: email, password },
    })
    token.guardar(access_token)
    setUsuario(await pedir<Usuario>('/usuarios/yo'))
  }

  const registrar = async (datos: DatosRegistro) => {
    await pedir('/auth/registro', { method: 'POST', json: datos })
    await ingresar(datos.email, datos.password)
  }

  const salir = () => {
    token.borrar()
    setUsuario(null)
  }

  return (
    <SesionContext.Provider value={{ usuario, cargando, ingresar, registrar, salir }}>{children}</SesionContext.Provider>
  )
}

export function useSesion() {
  const sesion = useContext(SesionContext)
  if (!sesion) throw new Error('useSesion debe usarse dentro de SesionProvider')
  return sesion
}
