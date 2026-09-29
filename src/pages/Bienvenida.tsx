import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Building2, Handshake, Lightbulb, Sparkles, Target, UserRoundSearch } from 'lucide-react'
import { apiHabilitada, pedir } from '@/lib/http'

interface Cifras {
  proyectos: number
  actores: number
  oportunidades_abiertas: number
  personas: number
}

const FUNCIONES = [
  {
    icono: Lightbulb,
    titulo: 'Todos los proyectos en un lugar',
    texto: 'Semilleros, grupos de investigación, trabajos de grado e iniciativas de extensión, con su estado, avance y necesidades.',
  },
  {
    icono: UserRoundSearch,
    titulo: 'Colaboradores sugeridos por IA',
    texto: 'La plataforma compara lo que necesita cada proyecto con las habilidades e intereses de estudiantes y docentes.',
  },
  {
    icono: Target,
    titulo: 'Convocatorias afines',
    texto: 'Recomienda fondos, mentorías e infraestructura según el área, los ODS y la descripción de tu proyecto, y explica por qué.',
  },
  {
    icono: Handshake,
    titulo: 'Alianzas con seguimiento',
    texto: 'Solicita unirte a un proyecto o invita a alguien; cada alianza queda registrada con su estado.',
  },
  {
    icono: Building2,
    titulo: 'Actores de la región',
    texto: 'Empresas, entidades públicas, comunidades y ONG vinculadas a los proyectos de la universidad.',
  },
  {
    icono: Sparkles,
    titulo: 'Búsqueda por significado',
    texto: 'Escribe lo que buscas con tus palabras y encuentra proyectos y oportunidades relacionadas, aunque no usen los mismos términos.',
  },
]

const PASOS = [
  ['Crea tu cuenta', 'Con tu cuenta de Google de la UFPSO o con tu correo institucional, que confirmas desde tu bandeja.'],
  ['Completa tu perfil', 'Cuéntanos tus habilidades e intereses para recibir sugerencias a tu medida.'],
  ['Registra o únete', 'Publica tu proyecto o solicita unirte a uno. La IA te propone colaboradores y convocatorias.'],
]

/** Página de inicio para visitantes: qué es Proyecta y cómo entrar. No muestra datos de proyectos. */
export function Bienvenida() {
  const [cifras, setCifras] = useState<Cifras | null>(null)

  useEffect(() => {
    if (apiHabilitada) pedir<Cifras>('/publico/cifras').then(setCifras).catch(() => setCifras(null))
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-20">
      <section className="grid items-center gap-10 lg:grid-cols-[1.2fr_1fr]">
        <div>
          <p className="inline-flex rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-800 ring-1 ring-brand-200 dark:bg-brand-500/12 dark:text-brand-200 dark:ring-brand-500/25">
            UFPS Ocaña · ODS 17 Alianzas para lograr los objetivos
          </p>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-balance text-slate-900 sm:text-5xl dark:text-white">
            Conecta tus proyectos con las personas y oportunidades que necesitan
          </h1>
          <p className="mt-5 max-w-xl text-lg text-pretty text-slate-600 dark:text-slate-400">
            Proyecta centraliza las iniciativas de la universidad y usa inteligencia artificial para encontrar
            colaboradores, aliados y convocatorias para cada una.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/registro" className="btn-primary px-5 py-2.5 text-base">
              Crear mi cuenta <ArrowRight size={17} aria-hidden />
            </Link>
            <Link to="/ingresar" className="btn-ghost px-5 py-2.5 text-base">Ya tengo cuenta</Link>
          </div>
          <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">
            Para estudiantes, docentes y administrativos con correo @ufpso.edu.co, y aliados externos.
          </p>
        </div>

        <div className="card relative overflow-hidden p-6">
          <div className="absolute -top-24 -right-24 h-56 w-56 rounded-full bg-accent-500/15 blur-3xl" aria-hidden />
          <div className="absolute -bottom-24 -left-24 h-56 w-56 rounded-full bg-brand-500/15 blur-3xl" aria-hidden />
          <p className="relative text-sm font-medium text-slate-500 dark:text-slate-400">Hoy en Proyecta</p>
          <dl className="relative mt-4 grid grid-cols-2 gap-5">
            <Cifra etiqueta="Proyectos registrados" valor={cifras?.proyectos} />
            <Cifra etiqueta="Personas" valor={cifras?.personas} />
            <Cifra etiqueta="Actores aliados" valor={cifras?.actores} />
            <Cifra etiqueta="Convocatorias abiertas" valor={cifras?.oportunidades_abiertas} />
          </dl>
          <p className="relative mt-6 rounded-lg bg-slate-50 p-3 text-xs text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
            El detalle de los proyectos, las personas y las convocatorias solo es visible para usuarios registrados.
          </p>
        </div>
      </section>

      <section>
        <h2 className="text-center text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Qué puedes hacer</h2>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FUNCIONES.map(({ icono: Icono, titulo, texto }) => (
            <article key={titulo} className="card p-5">
              <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-50 text-brand-700 dark:bg-brand-500/12 dark:text-brand-300">
                <Icono size={18} aria-hidden />
              </span>
              <h3 className="mt-4 font-semibold text-slate-900 dark:text-white">{titulo}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{texto}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="card p-8">
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">Cómo empezar</h2>
        <ol className="mt-6 grid gap-6 md:grid-cols-3">
          {PASOS.map(([titulo, texto], i) => (
            <li key={titulo} className="flex gap-4">
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-linear-to-br from-brand-600 to-accent-500 text-sm font-semibold text-white">
                {i + 1}
              </span>
              <div>
                <h3 className="font-medium text-slate-900 dark:text-white">{titulo}</h3>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{texto}</p>
              </div>
            </li>
          ))}
        </ol>
        <Link to="/registro" className="btn-primary mt-8">
          Empezar ahora <ArrowRight size={16} aria-hidden />
        </Link>
      </section>
    </div>
  )
}

function Cifra({ etiqueta, valor }: { etiqueta: string; valor: number | undefined }) {
  return (
    <div className="flex flex-col-reverse">
      <dt className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{etiqueta}</dt>
      <dd className="text-3xl font-semibold text-slate-900 tabular-nums dark:text-white">{valor ?? '—'}</dd>
    </div>
  )
}
