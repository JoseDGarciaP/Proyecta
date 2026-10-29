/** Reglas de las contraseñas nuevas. La API (app/core/security.py) aplica las mismas. */
export const CONTRASENA_MIN = 8
export const CONTRASENA_MAX = 20

export interface Requisito {
  texto: string
  cumple: boolean
}

export function requisitosContrasena(password: string): Requisito[] {
  const caracteres = [...password]
  return [
    { texto: `Entre ${CONTRASENA_MIN} y ${CONTRASENA_MAX} caracteres`, cumple: caracteres.length >= CONTRASENA_MIN && caracteres.length <= CONTRASENA_MAX },
    { texto: 'Una mayúscula', cumple: /\p{Lu}/u.test(password) },
    { texto: 'Una minúscula', cumple: /\p{Ll}/u.test(password) },
    { texto: 'Un número', cumple: /\p{Nd}/u.test(password) },
    { texto: 'Un símbolo (! @ # - _ …)', cumple: /[^\p{L}\p{N}\s]/u.test(password) },
  ]
}

export const contrasenaValida = (password: string) => requisitosContrasena(password).every((r) => r.cumple)
