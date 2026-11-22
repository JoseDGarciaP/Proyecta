# Manual de usuario de Proyecta

Este manual explica cómo usar Proyecta según tu rol. Cada sección tiene un espacio para la captura de pantalla
correspondiente (`docs/capturas/`). La documentación técnica de la API está en `/docs` del backend
(por ejemplo `https://<tu-backend>/docs`), generada automáticamente por FastAPI.

## Contenido

1. [Primeros pasos (todos los roles)](#1-primeros-pasos-todos-los-roles)
2. [Estudiante, docente y administrativo](#2-estudiante-docente-y-administrativo)
3. [Aliado externo](#3-aliado-externo)
4. [Administrador](#4-administrador)
5. [Preguntas frecuentes](#5-preguntas-frecuentes)

---

## 1. Primeros pasos (todos los roles)

### Crear la cuenta

1. Entra a **Registrarme**.
2. Escribe tu nombre, correo y una contraseña segura.
   - Estudiantes, docentes y administrativos usan el **correo institucional**, y además su **código** y **cédula**.
   - Los aliados externos pueden usar su correo personal y deben llenar los datos de su organización (ver sección 3).
3. Marca la casilla de **tratamiento de datos personales**. Sin ella no se puede crear la cuenta.
4. Abre el correo de verificación y sigue el enlace (vence en 24 horas).

> Captura: `capturas/registro.png`

### Ingresar y salir

- Después de **5 intentos fallidos** la cuenta se bloquea **15 minutos**.
- Si no usas la plataforma por **30 minutos**, la sesión se cierra sola.
- **Salir** cierra la sesión en todos tus dispositivos.
- ¿Olvidaste la contraseña? Usa **Restablecer contraseña** en la pantalla de ingreso.

### Mi perfil

En **Mi perfil** completas habilidades, intereses (áreas y ODS) y programa. Con eso el asistente te sugiere
proyectos y convocatorias. Ahí también ves:

- Tus proyectos, alianzas, nivel, insignias y evidencias.
- **Mi historial**: toda tu actividad con filtro por tipo y año, para descargar en **Excel** o imprimir en **PDF**.
- **Notificaciones**: qué correos quieres recibir.

> Captura: `capturas/perfil.png`

### Notificaciones

La campana muestra solicitudes, respuestas, cambios en tus proyectos, convocatorias por cerrar y avisos de la
cuenta. Puedes marcarlas como leídas, **archivarlas** o eliminarlas. Las de más de 90 días se archivan solas y
siguen disponibles en la pestaña **Archivadas**.

---

## 2. Estudiante, docente y administrativo

### Registrar un proyecto

1. **Proyectos → Registrar proyecto**.
2. Llena título, resumen, **problema**, **objetivos**, descripción, lo que necesita, presupuesto y fechas.
3. Elige el **área principal** y, si aplica, **áreas adicionales**.
4. Marca los ODS y los actores vinculados.

Cada cambio queda en el **historial de cambios** del proyecto y se le avisa al equipo.

> Captura: `capturas/proyecto-formulario.png`

### La ficha del proyecto

- **Documentos adjuntos**: el equipo sube PDF, DOCX, PNG o JPG.
- **Observaciones**: cualquier persona con cuenta deja comentarios; quien escribió una puede editarla o borrarla.
- **Aportes del equipo**: cada miembro registra lo que aportó (horas, dinero, materiales) y el responsable lo valida.
- **Eliminar**: pide un motivo. Si el proyecto tiene colaboradores no se borra: se **archiva** y se les avisa.
- **Exportar ficha PDF**: imprime la ficha.

> Captura: `capturas/proyecto-ficha.png`

### Colaborar

- **Solicitar unirme**: llena el formato (tipo de aporte, habilidades, horas, motivación). El responsable acepta
  o rechaza con un motivo.
- Como responsable puedes **invitar** personas, **cambiar su rol**, **retirarlas** con un motivo o
  **hacer responsable** a otro miembro antes de salir del proyecto.
- Si sales de un proyecto o te retiran, la alianza queda como **anulada** en tu historial con el motivo.

### Asistente de IA

En la ficha, **Analizar** genera un resumen, fortalezas, mejoras sugeridas y convocatorias afines.

- Las mejoras citan los **proyectos similares** en que se basan; marca si te fueron **útiles o no**.
- Cada convocatoria sugerida se puede **Aceptar** o **Descartar** (con motivo). Lo descartado no se vuelve a sugerir.
- En **Posibles colaboradores** ajustas cuánto pesan las habilidades frente al perfil completo.
- **Borrador de postulación** redacta una carta para la convocatoria.

### Convocatorias

En **Oportunidades** filtras por área, ODS y tipo, y postulas un proyecto. Te avisamos **7 días y 1 día antes del
cierre** de las convocatorias recomendadas para tus proyectos o afines a tus intereses, y cuando cambian sus fechas.

---

## 3. Aliado externo

1. Al registrarte elige **Aliado externo** y llena: tipo de organización, NIT o documento, razón social,
   teléfono y sector.
2. Tu cuenta queda **pendiente** hasta que un administrador la apruebe. Te llegará un correo con la decisión;
   si la rechazan, verás el motivo.
3. Ya aprobado, completa tu ficha de aliado en **Mi perfil** (sitio web, descripción) y aparecerás en el
   **directorio de aliados** de **Actores**.
4. **Mi historial** muestra tus alianzas y aportes y se descarga en Excel o PDF.

> Captura: `capturas/aliado-registro.png`

---

## 4. Administrador

El **Panel de administración** tiene una pestaña por tarea. Cada pestaña aparece solo si tu rol tiene el permiso.

| Pestaña | Qué hace |
| --- | --- |
| Resumen | Indicadores generales y **Por periodo**: proyectos por programa y área, evolución mensual, éxito de postulaciones y recomendaciones aceptadas. Exporta el panel a **Excel** con la fecha de generación, y el reporte institucional en CSV. |
| Usuarios | Buscar, crear, activar o desactivar cuentas y cambiar roles. |
| Aliados | Aprobar o rechazar (con motivo) a los aliados pendientes y corregir su documento. |
| Moderación | **Ocultar** proyectos (se pueden **restaurar**) o eliminarlos, ocultar observaciones, gestionar oportunidades (las que tienen postulaciones se archivan) y postulaciones (exportables a **Excel**). |
| Colaboración | Motivos de aprobación y rechazo, tipos de aporte y plantillas. |
| Áreas y ODS, Ajustes | Catálogos y parámetros generales. |
| Roles y permisos | Matriz de permisos por rol. |
| Insignias, Niveles y XP, Evidencias | Gamificación y revisión de certificados. |
| Bitácora | Quién hizo qué y cuándo, con filtros por acción, **persona** y **fechas**. |

> Captura: `capturas/admin-resumen.png`

### Tareas programadas

La API corre cada hora la tarea que envía los avisos de cierre y archiva las notificaciones viejas. Si
`RESUMEN_AUTOMATICO=false`, prográmala con cron: `python -m scripts.tarea_diaria`.

---

## 5. Preguntas frecuentes

**No me llegó el correo de verificación.** Revisa spam y pide uno nuevo desde la pantalla de ingreso.

**Mi cuenta dice que está bloqueada.** Espera 15 minutos o restablece la contraseña.

**¿Por qué no veo un proyecto que existía?** Pudo ser archivado por su responsable u ocultado por moderación.

**¿Cómo cambio qué correos recibo?** En **Mi perfil → Notificaciones**.
