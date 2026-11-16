import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

const CONTACTO = 'notificaciones.proyecta.app@gmail.com'
const ACTUALIZADA = '16 de noviembre de 2026'

function Seccion({ titulo, children }: { titulo: string; children: ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="text-base font-semibold text-slate-900 dark:text-white">{titulo}</h2>
      <div className="space-y-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{children}</div>
    </section>
  )
}

/** Política de tratamiento de datos personales (Ley 1581 de 2012). Pública: la enlazan el registro y Google. */
export function Privacidad() {
  return (
    <article className="mx-auto max-w-3xl space-y-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
          Política de privacidad y tratamiento de datos
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Última actualización: {ACTUALIZADA}</p>
      </header>

      <div className="card space-y-7 p-6">
        <Seccion titulo="1. Quién trata tus datos">
          <p>
            Proyecta es una plataforma académica desarrollada por un equipo de estudiantes para centralizar proyectos e
            iniciativas y conectarlos con actores y oportunidades de apoyo. El equipo de Proyecta es el responsable del
            tratamiento de tus datos. Contacto: <a className="font-medium text-brand-700 underline dark:text-brand-300" href={`mailto:${CONTACTO}`}>{CONTACTO}</a>.
          </p>
        </Seccion>

        <Seccion titulo="2. Qué datos recogemos">
          <ul className="list-disc space-y-1 pl-5">
            <li><b>Datos de tu cuenta:</b> nombre, correo electrónico, rol (estudiante, docente, administrativo o aliado externo) y programa, dependencia u organización. Tu contraseña se guarda cifrada; nadie puede leerla.</li>
            <li><b>Si entras con Google:</b> solo recibimos tu nombre y tu correo verificado. No accedemos a tu Gmail, tus archivos ni tus contactos.</li>
            <li><b>Lo que publicas:</b> proyectos, descripciones, habilidades e intereses, postulaciones, mensajes en los chats de proyectos y solicitudes, y las evidencias o certificados que subes.</li>
            <li><b>Actividad en la plataforma:</b> experiencia (XP), nivel, insignias y notificaciones, y un registro de las acciones de los administradores.</li>
          </ul>
        </Seccion>

        <Seccion titulo="3. Para qué los usamos">
          <ul className="list-disc space-y-1 pl-5">
            <li>Crear y proteger tu cuenta, y confirmar que tu correo es tuyo.</li>
            <li>Mostrar tus proyectos y tu perfil a otros usuarios de la plataforma, y permitir la colaboración entre equipos, actores y oportunidades.</li>
            <li>Enviarte avisos por correo y dentro de la plataforma (confirmaciones, invitaciones, respuestas a tus solicitudes).</li>
            <li>Sugerir proyectos parecidos y generar análisis o resúmenes de proyectos con inteligencia artificial.</li>
          </ul>
          <p>No vendemos ni cedemos tus datos, y no los usamos para publicidad.</p>
        </Seccion>

        <Seccion titulo="4. Con quién se comparten">
          <p>Solo con los servicios necesarios para que la plataforma funcione, que actúan como encargados del tratamiento:</p>
          <ul className="list-disc space-y-1 pl-5">
            <li><b>Contabo</b>: servidor donde se guardan la base de datos y los archivos (ubicado en Estados Unidos).</li>
            <li><b>Brevo</b>: envío de los correos de la plataforma.</li>
            <li><b>Groq</b>: procesa el texto de un proyecto cuando alguien usa la función «Analizar». No se le envían contraseñas ni datos de contacto.</li>
            <li><b>Google</b>: solo si eliges «Continuar con Google», para confirmar tu identidad.</li>
          </ul>
          <p>
            Algunos de estos servicios están fuera de Colombia. Al usar Proyecta autorizas esa transferencia, que se hace
            únicamente para las finalidades descritas aquí.
          </p>
        </Seccion>

        <Seccion titulo="5. Cuánto tiempo los guardamos">
          <p>
            Mientras tengas una cuenta activa y la plataforma esté en funcionamiento. Si pides eliminar tu cuenta, o cuando
            la plataforma deje de operar, se borran tus datos y las copias de seguridad que los contengan se eliminan en
            un plazo máximo de 14 días.
          </p>
        </Seccion>

        <Seccion titulo="6. Tus derechos">
          <p>De acuerdo con la Ley 1581 de 2012 (Habeas Data) y el Decreto 1377 de 2013, puedes:</p>
          <ul className="list-disc space-y-1 pl-5">
            <li>Conocer, actualizar y rectificar tus datos (la mayoría puedes editarlos tú mismo en «Mi perfil»).</li>
            <li>Pedir prueba de la autorización que nos diste y saber cómo hemos usado tus datos.</li>
            <li>Revocar tu autorización y pedir que eliminemos tus datos, cuando no exista un deber legal de conservarlos.</li>
            <li>Presentar quejas ante la Superintendencia de Industria y Comercio si consideras que no se respetaron tus derechos.</li>
          </ul>
          <p>
            Para ejercerlos, escribe a <a className="font-medium text-brand-700 underline dark:text-brand-300" href={`mailto:${CONTACTO}`}>{CONTACTO}</a> desde
            el correo de tu cuenta. Respondemos consultas en un máximo de 10 días hábiles y reclamos en un máximo de 15 días hábiles.
          </p>
        </Seccion>

        <Seccion titulo="7. Seguridad">
          <p>
            La plataforma funciona solo por HTTPS, las contraseñas se guardan cifradas, la base de datos no es accesible desde
            internet y el acceso al servidor está restringido al equipo administrador.
          </p>
        </Seccion>

        <Seccion titulo="8. Aceptación y cambios">
          <p>
            Al crear una cuenta o entrar con Google aceptas esta política. Si la cambiamos de forma importante, te lo
            avisaremos dentro de la plataforma o por correo.
          </p>
        </Seccion>
      </div>

      <p className="text-center text-sm">
        <Link to="/" className="font-medium text-brand-700 underline dark:text-brand-300">Volver a Proyecta</Link>
      </p>
    </article>
  )
}
