import { createClient, type SupabaseClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

/** true cuando hay credenciales; si no, la app corre en modo demo con datos locales. */
export const supabaseHabilitado = Boolean(url && anonKey)

export const supabase: SupabaseClient | null = supabaseHabilitado
  ? createClient(url as string, anonKey as string, {
      auth: { persistSession: true, autoRefreshToken: true },
    })
  : null
