"""Catálogo de permisos: cada acción que un rol puede o no hacer. Los roles guardan una lista de estas claves."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Permiso:
    clave: str
    grupo: str
    nombre: str
    descripcion: str
    solo_admin: bool = False  # no se puede dar a otros roles (evita que alguien se dé más permisos)


PERMISOS: list[Permiso] = [
    Permiso("proyectos.crear", "Proyectos", "Registrar proyectos", "Crear proyectos nuevos y quedar como responsable."),
    Permiso("proyectos.moderar", "Proyectos", "Editar o quitar proyectos ajenos", "Modificar o eliminar cualquier proyecto y retirar a sus miembros."),
    Permiso("colaboracion.solicitar", "Colaboración", "Pedir unirse a proyectos", "Enviar solicitudes para colaborar en proyectos de otros."),
    Permiso("colaboracion.invitar", "Colaboración", "Invitar personas", "Invitar a otras personas a sus propios proyectos."),
    Permiso("chat.usar", "Colaboración", "Usar los chats", "Escribir en el chat de sus equipos y en la conversación de sus solicitudes."),
    Permiso("chat.moderar", "Colaboración", "Moderar chats", "Leer cualquier chat y eliminar mensajes de otras personas."),
    Permiso("usuarios.ver", "Directorio", "Ver perfiles de personas", "Ver el perfil público, logros y proyectos de otras personas."),
    Permiso("actores.ver", "Directorio", "Ver actores", "Consultar el directorio de actores aliados."),
    Permiso("oportunidades.ver", "Directorio", "Ver oportunidades", "Consultar convocatorias, fondos y mentorías."),
    Permiso("oportunidades.postular", "Directorio", "Postular proyectos a oportunidades", "Postular sus proyectos a convocatorias, fondos y mentorías."),
    Permiso("evidencias.subir", "Colaboración", "Subir certificados y evidencias", "Adjuntar certificados o archivos (propios o de sus proyectos) para que la administración los revise."),
    Permiso("ia.usar", "Directorio", "Usar la IA", "Análisis de proyectos, búsqueda semántica y sugerencias."),
    Permiso("actores.gestionar", "Gestión de contenido", "Gestionar actores", "Crear, editar y eliminar actores."),
    Permiso("oportunidades.gestionar", "Gestión de contenido", "Gestionar oportunidades", "Crear, editar y eliminar oportunidades y decidir las postulaciones."),
    Permiso("admin.resumen", "Panel de administración", "Ver estadísticas", "Pestaña «Resumen» del panel."),
    Permiso("admin.usuarios", "Panel de administración", "Gestionar usuarios", "Crear cuentas, cambiar roles, activar o desactivar."),
    Permiso("admin.insignias", "Panel de administración", "Gestionar insignias", "Crear insignias, otorgarlas y retirarlas."),
    Permiso("admin.experiencia", "Panel de administración", "Niveles y experiencia", "Niveles, puntos por acción y ajustes manuales de XP."),
    Permiso("admin.evidencias", "Panel de administración", "Revisar evidencias", "Aprobar o rechazar certificados y dar experiencia por ellos."),
    Permiso("admin.colaboracion", "Panel de administración", "Motivos, aportes y plantillas", "Catálogos del flujo de colaboración."),
    Permiso("admin.catalogos", "Panel de administración", "Áreas y ODS", "Catálogos de áreas y nombres de los ODS."),
    Permiso("admin.moderacion", "Panel de administración", "Moderación", "Retirar proyectos con motivo (y gestionar oportunidades y actores si tiene esos permisos)."),
    Permiso("admin.ajustes", "Panel de administración", "Ajustes generales", "Dominios permitidos y correos de alerta."),
    Permiso("admin.bitacora", "Panel de administración", "Ver la bitácora", "Historial de acciones de administración."),
    Permiso("admin.roles", "Panel de administración", "Roles y permisos", "Crear roles y cambiar sus permisos. Solo el rol Administrador.", solo_admin=True),
]

POR_CLAVE = {p.clave: p for p in PERMISOS}
TODOS = frozenset(POR_CLAVE)
ASIGNABLES = frozenset(p.clave for p in PERMISOS if not p.solo_admin)

# Lo que podía hacer cualquier persona registrada antes de existir los permisos.
BASICOS = [
    "proyectos.crear", "colaboracion.solicitar", "colaboracion.invitar", "chat.usar",
    "usuarios.ver", "actores.ver", "oportunidades.ver", "ia.usar", "oportunidades.postular", "evidencias.subir",
]


def nombre(clave: str) -> str:
    return POR_CLAVE[clave].nombre if clave in POR_CLAVE else clave
