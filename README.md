# Proyecta

Plataforma para **centralizar proyectos e iniciativas** y facilitar su articulación con actores
y oportunidades de apoyo. Reúne en un solo lugar el registro y seguimiento de proyectos, el
directorio de actores, la cartelera de convocatorias y un asistente de IA que resume proyectos,
sugiere oportunidades afines y propone colaboradores.

## Objetivo

Que estudiantes, docentes, administrativos y aliados externos puedan dar a conocer sus
iniciativas, encontrar personas con las habilidades que necesitan, sumar aliados y postularse a
oportunidades de apoyo, mientras la institución tiene una visión completa de lo que se está
haciendo, evita proyectos duplicados y reconoce la participación.

## Cómo funciona

### Acceso

Sin sesión solo se ve la página de bienvenida con cifras generales; proyectos, personas, actores,
oportunidades e IA exigen una cuenta con el correo confirmado.

- **Registro con correo y contraseña:** se envía un enlace de confirmación que vence en 48 horas.
- **Continuar con Google:** con una cuenta del dominio institucional, que queda verificada de una vez.
- **Correos verídicos:** antes de crear la cuenta se revisa el formato, se corrigen errores de
  tipeo frecuentes (`gmial.com` → «¿quisiste decir gmail.com?»), se rechazan correos temporales y
  se confirma que el dominio recibe correo. Una cuenta sin confirmar no aparta el correo, así que
  el dueño real siempre puede registrarse.

### Proyectos y panel

El panel muestra métricas generales (proyectos por estado, por área y por mes, presupuesto y
avance promedio). Cada proyecto tiene su ficha con área, ODS, estado, avance, equipo, necesidades
y conversación propia.

### Perfil y alianzas

Cada persona tiene **Mi perfil**: sus datos, habilidades e intereses, los proyectos que registró
o donde colabora, sus alianzas y sugerencias personalizadas. Una alianza es una solicitud para
unirse a un proyecto (la responde quien lo registró) o una invitación (la responde el invitado);
al aceptarse, la persona queda como colaboradora y el historial se conserva con su estado.

### Colaboración con formato fijo y motivos

Pedir unirse a un proyecto o invitar a alguien usa siempre el mismo formulario: **rol o tipo de
aporte**, **qué aporta o qué se espera**, **habilidades**, **horas por semana**, **motivación** y
una nota opcional. La conversación de cada solicitud ofrece **plantillas de mensaje** según quién
escribe.

Aprobar o rechazar exige elegir un **motivo** del catálogo y admite un comentario, obligatorio si
el motivo lo pide. Al aprobar, la persona queda como miembro con el rol propuesto.

### Asistente de IA y similitud

- **Resúmenes de proyectos** redactados por un modelo de lenguaje. Si el modelo no responde, el
  resumen sale de reglas locales y la interfaz lo marca como simulado.
- **Recomendación de oportunidades** que explica por qué se sugiere cada una (área, ODS en común,
  etiquetas y vigencia; solo convocatorias abiertas).
- **Similitud semántica** entre textos, en varios lugares de la plataforma:

| Función | Dónde se ve |
|---|---|
| Proyectos que buscan un perfil como el mío | Mi perfil → Sugerencias para ti |
| Oportunidades para mis proyectos | Mi perfil y Asistente de articulación |
| Proyectos similares (articularse o evitar duplicados) | Detalle del proyecto |
| Posibles colaboradores según «Lo que necesita» | Detalle del proyecto (solo su responsable) |
| Búsqueda por significado de convocatorias | Oportunidades |

### Notificaciones

Cada evento crea un aviso en la **campana** del encabezado y, si corresponde, un **correo**:

- solicitud o invitación nueva → a quien debe responder, con la ficha completa;
- aprobada, rechazada o retirada → a la otra persona, con el motivo y el comentario;
- mensajes sin leer → un solo resumen por persona;
- cambios hechos por un administrador (rol, cuenta desactivada o reactivada, proyecto retirado).

Cada persona elige en su perfil qué correos recibe.

### Logros: insignias, niveles y experiencia

- **Insignias:** tres tipos (Logro, Condecoración y Reconocimiento). Pueden ser automáticas, con
  uno o varios requisitos (proyectos registrados o finalizados, colaboraciones, horas
  comprometidas, antigüedad, otras insignias…), o manuales, otorgadas a una persona, a varias o a
  todo el equipo de un proyecto, con motivo y fecha. Pueden vencer y se pueden retirar.
- **Experiencia (XP):** cada acción suma puntos según una tabla editable (entrar cada día,
  completar el perfil, registrar, avanzar y finalizar proyectos, colaborar, postular a
  convocatorias, ganar insignias, evidencias aprobadas…). Nada suma dos veces por lo mismo.
- **Niveles:** Novato, Curioso, Aprendiz, Colaborador, Descubridor, Conocedor, Experto, Genio y
  Leyenda. Piden XP mínima e insignias; al subir llega un aviso y se muestra una celebración. El
  nivel aparece junto al nombre y hay un ranking por semana, mes o de siempre.
- **Postulaciones:** el equipo de un proyecto lo postula a una oportunidad explicando por qué
  encaja; quien gestiona oportunidades lo marca como seleccionado o no, y el equipo recibe aviso y XP.
- **Evidencias:** certificados, constancias, informes o fotos que se suben en el perfil o en el
  proyecto; un administrador los revisa y decide cuánta XP dar o los rechaza con un motivo.

### Administración

- **Resumen:** usuarios, solicitudes por estado, tasa de aprobación, motivos y aportes más usados.
- **Usuarios:** buscar, filtrar, cambiar rol, activar o desactivar, editar datos y crear cuentas.
- **Colaboración:** motivos de aprobación y rechazo, tipos de aporte y plantillas de mensaje.
- **Áreas y ODS**, **Moderación** de proyectos, oportunidades y actores, y **Ajustes** generales.
- **Roles y permisos:** matriz de permisos por acción para cada rol y roles nuevos (p. ej.
  «Coordinador de semillero»). La interfaz oculta lo que el rol no puede hacer y la API lo rechaza.
- **Insignias**, **Niveles y XP** y **Evidencias**.
- **Bitácora:** quién hizo qué y cuándo.

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Interfaz | React, React Router, Vite, TypeScript, Tailwind CSS, Recharts |
| API | Python, FastAPI, SQLAlchemy, Alembic |
| Base de datos | PostgreSQL con pgvector |
| IA | Modelos de lenguaje (Groq u Ollama) y sentence-transformers |

La arquitectura y el modelo de datos están en [`docs/arquitectura.md`](docs/arquitectura.md).
