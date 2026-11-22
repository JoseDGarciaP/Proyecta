import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { apiHabilitada, pedir, token } from './http'
import type { Rol, Usuario } from './types'
import type { DatosAliado } from './aliados'

export interface DatosRegistro {
  nombre: string
  email: string
  password: string
  rol: Rol
  programa: string | null
  /** Código del enlace de una invitación a un proyecto (confirma el correo si coincide). */
  invitacion?: string
  /** Datos institucionales (estudiantes, docentes y administrativos). */
  codigo?: string
  cedula?: string
  sexo?: string
  /** Autorización de tratamiento de datos personales (Ley 1581 de 2012). */
  acepta_datos: boolean
  /** Solo para aliados externos (Ep4-Hu12). */
  aliado?: DatosAliado
}

/** Minutos sin actividad tras los que la sesión se cierra sola (Ep4-Hu2). */
const INACTIVIDAD_MINUTOS = 30

interface Sesion {
  usuario: Usuario | null
  cargando: boolean
  ingresar: (email: string, password: string) => Promise<void>
  /** Crea la cuenta; queda pendiente de confirmar el correo (no inicia sesión), salvo que llegue
   * con el código de una invitación enviada a ese mismo correo: entonces ya queda confirmada. */
  registrar: (datos: DatosRegistro) => Promise<Usuario>
  /** Confirma el correo con el token del enlace e inicia sesión. */
  verificarCorreo: (tokenCorreo: string) => Promise<void>
  reenviarVerificacion: (email: string) => Promise<void>
  ingresarConGoogle: (credential: string) => Promise<void>
  /** Envía el enlace para elegir otra contraseña (responde igual aunque el correo no exista). */
  recuperarContrasena: (email: string) => Promise<void>
  /** Guarda la contraseña nueva con el token del enlace e inicia sesión. */
  restablecerContrasena: (tokenCorreo: string, password: string) => Promise<void>
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
    return pedir<Usuario>('/auth/registro', { method: 'POST', json: datos })
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

  const recuperarContrasena = async (email: string) => {
    await pedir('/auth/recuperar', { method: 'POST', json: { email } })
  }

  const restablecerContrasena = async (tokenCorreo: string, password: string) => {
    const { access_token } = await pedir<{ access_token: string }>('/auth/restablecer', {
      method: 'POST',
      json: { token: tokenCorreo, password },
    })
    await iniciar(access_token)
  }

  const salir = () => {
    // Invalida el token en el servidor; si falla (sin red) igual se borra en este navegador.
    if (apiHabilitada && token.leer()) pedir('/auth/salir', { method: 'POST' }).catch(() => undefined)
    token.borrar()
    setUsuario(null)
  }

  const salirRef = useRef(salir)
  useEffect(() => {
    salirRef.current = salir
  })

  // Cierre por inactividad: cualquier clic, tecla o desplazamiento reinicia el contador.
  useEffect(() => {
    if (!usuario) return
    let temporizador = window.setTimeout(() => salirRef.current(), INACTIVIDAD_MINUTOS * 60_000)
    const reiniciar = () => {
      window.clearTimeout(temporizador)
      temporizador = window.setTimeout(() => salirRef.current(), INACTIVIDAD_MINUTOS * 60_000)
    }
    const eventos = ['mousedown', 'keydown', 'scroll', 'touchstart'] as const
    eventos.forEach((e) => window.addEventListener(e, reiniciar, { passive: true }))
    return () => {
      window.clearTimeout(temporizador)
      eventos.forEach((e) => window.removeEventListener(e, reiniciar))
    }
  }, [usuario])

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
        recuperarContrasena,
        restablecerContrasena,
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
