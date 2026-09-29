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
  /** Crea la cuenta; queda pendiente de confirmar el correo (no inicia sesión). */
  registrar: (datos: DatosRegistro) => Promise<void>
  /** Confirma el correo con el token del enlace e inicia sesión. */
  verificarCorreo: (tokenCorreo: string) => Promise<void>
  reenviarVerificacion: (email: string) => Promise<void>
  ingresarConGoogle: (credential: string) => Promise<void>
  salir: () => void
  /** Actualiza los datos del usuario tras editar el perfil. */
  refrescar: (u: Usuario) => void
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

  const iniciar = async (accessToken: string) => {
    token.guardar(accessToken)
    setUsuario(await pedir<Usuario>('/usuarios/yo'))
  }

  const ingresar = async (email: string, password: string) => {
    const { access_token } = await pedir<{ access_token: string }>('/auth/login', {
      method: 'POST',
      form: { username: email, password },
    })
    await iniciar(access_token)
  }

  const registrar = async (datos: DatosRegistro) => {
    await pedir('/auth/registro', { method: 'POST', json: datos })
  }

  const verificarCorreo = async (tokenCorreo: string) => {
    const { access_token } = await pedir<{ access_token: string }>('/auth/verificar', {
      method: 'POST',
      json: { token: tokenCorreo },
    })
    await iniciar(access_token)
  }

  const reenviarVerificacion = async (email: string) => {
    await pedir('/auth/reenviar-verificacion', { method: 'POST', json: { email } })
  }

  const ingresarConGoogle = async (credential: string) => {
    const { access_token } = await pedir<{ access_token: string }>('/auth/google', {
      method: 'POST',
      json: { credential },
    })
    await iniciar(access_token)
  }

  const salir = () => {
    token.borrar()
    setUsuario(null)
  }

  return (
    <SesionContext.Provider
      value={{
        usuario,
        cargando,
        ingresar,
        registrar,
        verificarCorreo,
        reenviarVerificacion,
        ingresarConGoogle,
        salir,
        refrescar: setUsuario,
      }}
    >
      {children}
    </SesionContext.Provider>
  )
}

export function useSesion() {
  const sesion = useContext(SesionContext)
  if (!sesion) throw new Error('useSesion debe usarse dentro de SesionProvider')
  return sesion
}
