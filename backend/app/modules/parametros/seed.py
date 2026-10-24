"""Valores iniciales de los parámetros. La migración 0007 y las pruebas los cargan; luego los edita el admin."""

MOTIVOS = [
    # (tipo, nombre, descripcion, requiere_comentario)
    ("aprobacion", "Perfil adecuado para el proyecto", "Sus habilidades e intereses coinciden con lo que se necesita.", False),
    ("aprobacion", "Aporta habilidades que faltaban", "Cubre un rol o conocimiento que el equipo no tenía.", False),
    ("aprobacion", "Disponibilidad de tiempo suficiente", "Puede dedicar las horas que el proyecto requiere.", False),
    ("aprobacion", "Recomendado por el equipo", "Algún miembro del equipo lo recomendó.", False),
    ("aprobacion", "Otro motivo", "Explica el motivo en el comentario.", True),
    ("rechazo", "El equipo ya está completo", "Por ahora no se necesitan más integrantes.", False),
    ("rechazo", "El perfil no coincide con lo que se necesita", "Las habilidades no corresponden a las necesidades actuales.", False),
    ("rechazo", "Disponibilidad de tiempo insuficiente", "Las horas disponibles no alcanzan para el trabajo previsto.", False),
    ("rechazo", "El proyecto está pausado o finalizando", "No hay actividades en las que pueda participar ahora.", False),
    ("rechazo", "No puedo asumir el compromiso", "Para invitaciones: no puedo participar en este momento.", False),
    ("rechazo", "Otro motivo", "Explica el motivo en el comentario.", True),
]

TIPOS_APORTE = [
    ("Desarrollo de software", "Programación, bases de datos, despliegue."),
    ("Diseño y experiencia de usuario", "Interfaces, prototipos, identidad visual."),
    ("Investigación", "Revisión de literatura, trabajo de campo, análisis."),
    ("Análisis de datos", "Estadística, visualización, modelos."),
    ("Gestión y coordinación", "Planeación, seguimiento, relación con aliados."),
    ("Comunicación y divulgación", "Redes, contenidos, presentaciones."),
    ("Asesoría o mentoría", "Acompañamiento docente o experto."),
    ("Trabajo técnico de campo", "Instalación, pruebas, mantenimiento."),
    ("Otro", "Descríbelo en el aporte."),
]

PLANTILLAS = [
    # (para, titulo, texto)
    ("responsable", "Pedir más información",
     "Hola, gracias por tu interés en el proyecto. Antes de decidir me gustaría saber un poco más: "
     "¿en qué proyectos o trabajos similares has participado y qué resultados obtuviste?"),
    ("responsable", "Confirmar disponibilidad",
     "Hola. El proyecto requiere reuniones semanales y entregas cada dos semanas. "
     "¿Puedes confirmar tu disponibilidad de horario para ese ritmo de trabajo?"),
    ("responsable", "Proponer una reunión",
     "Hola. Me gustaría conversar contigo unos 15 minutos para conocernos y contarte el plan del proyecto. "
     "¿Qué día y hora te queda bien esta semana?"),
    ("responsable", "Explicar las tareas",
     "Hola. Si te unes, tus primeras tareas serían: [describe las tareas]. "
     "¿Te sientes cómodo/a con ellas o prefieres otro tipo de aporte?"),
    ("solicitante", "Presentarme",
     "Hola, soy [tu nombre], de [programa o dependencia]. Me interesa el proyecto porque [motivo]. "
     "Puedo aportar en [habilidades] y tengo [horas] horas por semana."),
    ("solicitante", "Compartir experiencia",
     "Te cuento mi experiencia relacionada: [proyectos, cursos o trabajos]. "
     "Si quieres puedo compartir ejemplos de lo que he hecho."),
    ("solicitante", "Preguntar por el proyecto",
     "Hola. Antes de comprometerme quisiera saber: ¿en qué etapa está el proyecto, cómo se organiza el equipo "
     "y qué se esperaría de mí?"),
    ("todos", "Agradecer",
     "¡Muchas gracias por la información! Lo reviso y te respondo pronto."),
]


def sembrar(db) -> None:
    """Carga los valores iniciales en las tablas vacías (no toca lo que el admin ya configuró)."""
    from sqlalchemy import func, select

    from app.modules.parametros.models import Motivo, ParaPlantilla, Plantilla, TipoAporte, TipoMotivo

    if not db.scalar(select(func.count(Motivo.id))):
        db.add_all([
            Motivo(tipo=TipoMotivo(t), nombre=n, descripcion=d, requiere_comentario=c, orden=i)
            for i, (t, n, d, c) in enumerate(MOTIVOS)
        ])
    if not db.scalar(select(func.count(TipoAporte.id))):
        db.add_all([TipoAporte(nombre=n, descripcion=d, orden=i) for i, (n, d) in enumerate(TIPOS_APORTE)])
    if not db.scalar(select(func.count(Plantilla.id))):
        db.add_all([Plantilla(para=ParaPlantilla(p), titulo=t, texto=x, orden=i) for i, (p, t, x) in enumerate(PLANTILLAS)])
    db.commit()
