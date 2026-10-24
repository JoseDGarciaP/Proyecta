"""Insignias iniciales (la migración 0008 y las pruebas las cargan; luego las edita el admin)."""


def regla(*condiciones, modo="todas"):
    return {"modo": modo, "condiciones": [{"criterio": c, "umbral": u, "valor": v} for c, u, v in condiciones]}


INSIGNIAS = [
    # (nombre, descripcion, tipo, icono, color, reglas)
    ("Primer proyecto", "Registró su primer proyecto en la plataforma.", "logro", "rocket", "brand",
     regla(("proyectos_registrados", 1, None))),
    ("Emprendedor/a", "Ha registrado 3 proyectos.", "logro", "lightbulb", "amber", regla(("proyectos_registrados", 3, None))),
    ("Colaborador/a", "Se sumó a su primer proyecto de otro equipo.", "logro", "handshake", "accent", regla(("colaboraciones", 1, None))),
    ("Aliado/a constante", "Colabora en 5 proyectos de otros equipos.", "logro", "users", "violet", regla(("colaboraciones", 5, None))),
    ("Líder de equipo", "Sumó 3 personas a sus proyectos.", "logro", "flag", "emerald", regla(("integrantes_sumados", 3, None))),
    ("Proyecto cumplido", "Participó en un proyecto que llegó a «Finalizado».", "logro", "trophy", "amber",
     regla(("proyectos_finalizados", 1, None))),
    ("Perfil completo", "Completó su perfil: descripción, habilidades e intereses.", "logro", "badge_check", "sky",
     regla(("perfil_completo", 1, None))),
    ("Conversador/a", "Envió 50 mensajes en los chats de sus equipos.", "logro", "message", "accent", regla(("mensajes_enviados", 50, None))),
    ("Mención de honor", "Reconocimiento especial por un aporte destacado.", "condecoracion", "medal", "rose", None),
    ("Mentor/a destacado/a", "Acompañó y guió a otros equipos.", "reconocimiento", "graduation", "violet", None),
    ("Innovación", "Propuso una solución especialmente creativa.", "reconocimiento", "sparkles", "brand", None),
]


def sembrar(db) -> None:
    from sqlalchemy import func, select

    from app.modules.insignias.models import Insignia

    if not db.scalar(select(func.count(Insignia.id))):
        db.add_all([Insignia(nombre=n, descripcion=d, tipo=t, icono=i, color=c, reglas=r, orden=o)
                    for o, (n, d, t, i, c, r) in enumerate(INSIGNIAS)])
        db.commit()
