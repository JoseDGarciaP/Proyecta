"""Acciones y niveles iniciales (la migración 0010 y las pruebas los cargan; luego los edita el admin)."""

ACCIONES = [
    # (clave, nombre, descripcion, puntos, tope_diario)
    ("ingreso_diario", "Entrar a la plataforma", "Una vez al día.", 2, 1),
    ("perfil_completo", "Completar el perfil", "Descripción, habilidades e intereses. Una sola vez.", 30, None),
    ("proyecto_registrado", "Registrar un proyecto", "Por cada proyecto nuevo.", 50, None),
    ("proyecto_avanza", "Avanzar un proyecto", "Cada vez que el avance cruza un 10 % más (10, 20, 30…).", 15, None),
    ("proyecto_finalizado", "Finalizar un proyecto", "Para todo el equipo cuando el proyecto llega a «Finalizado».", 100, None),
    ("solicitud_enviada", "Pedir unirse a un proyecto", "Enviar una solicitud de colaboración.", 5, 5),
    ("invitacion_enviada", "Invitar a alguien", "Invitar a una persona a tu proyecto.", 3, 5),
    ("colaboracion_aprobada", "Ser aceptado en un proyecto", "Cuando aprueban tu solicitud o aceptas una invitación.", 40, None),
    ("integrante_sumado", "Sumar una persona al equipo", "Para el responsable, por cada persona que entra.", 20, None),
    ("mensaje_equipo", "Escribir en el chat del equipo", "Por mensaje, con tope diario.", 1, 20),
    ("postulacion_enviada", "Postular un proyecto a una convocatoria", "Por cada postulación.", 25, None),
    ("postulacion_aceptada", "Proyecto seleccionado en una convocatoria", "Para todo el equipo.", 150, None),
    ("insignia_obtenida", "Ganar una insignia", "Por cada insignia nueva.", 20, None),
    ("evidencia_aprobada", "Certificado o evidencia aprobada", "Valor sugerido; el admin decide cuánto dar en cada caso.", 30, None),
]

NIVELES = [
    # (nombre, descripcion, icono, color, xp_minima, insignias_minimas)
    ("Novato", "Recién llegado a Proyecta.", "sprout", "slate", 0, 0),
    ("Curioso", "Explora proyectos y oportunidades.", "eye", "sky", 50, 0),
    ("Aprendiz", "Ya participa y aprende con otros.", "book", "teal", 150, 1),
    ("Colaborador", "Aporta en equipos de forma activa.", "handshake", "emerald", 350, 2),
    ("Descubridor", "Encuentra oportunidades y las aprovecha.", "compass", "lime", 700, 3),
    ("Conocedor", "Domina la plataforma y orienta a otros.", "lightbulb", "amber", 1200, 4),
    ("Experto", "Referente por su trabajo en proyectos.", "medal", "orange", 2000, 6),
    ("Genio", "Impacto destacado y constante.", "brain", "violet", 3200, 8),
    ("Leyenda", "Lo máximo en Proyecta.", "crown", "brand", 5000, 10),
]


def sembrar(db) -> None:
    from sqlalchemy import func, select

    from app.modules.experiencia.models import AccionXP, Nivel

    if not db.scalar(select(func.count(AccionXP.clave))):
        db.add_all([AccionXP(clave=c, nombre=n, descripcion=d, puntos=p, tope_diario=t, orden=i)
                    for i, (c, n, d, p, t) in enumerate(ACCIONES)])
    if not db.scalar(select(func.count(Nivel.id))):
        db.add_all([Nivel(nombre=n, descripcion=d, icono=i, color=c, xp_minima=x, insignias_minimas=m, insignias_requeridas=[])
                    for n, d, i, c, x, m in NIVELES])
    db.commit()
