"""experiencia (XP) y niveles, postulaciones a oportunidades y evidencias (certificados)

Revision ID: 0010
Revises: 0009
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Copia fija de app/modules/experiencia/seed.py al momento de esta migración (el seed puede cambiar después).
ACCIONES = [
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
# Permisos nuevos que reciben los roles base (el admin los tiene todos siempre).
PERMISOS_NUEVOS = ["oportunidades.postular", "evidencias.subir"]
ROLES_BASE = ["estudiante", "docente", "administrativo", "aliado"]

_roles = sa.table('roles', sa.column('clave', sa.String), sa.column('permisos', sa.JSON), sa.column('sistema', sa.Boolean))


def _permisos(valor) -> list[str]:
    return list(valor if isinstance(valor, list) else json.loads(valor or "[]"))


def upgrade() -> None:
    acciones = op.create_table('acciones_xp',
    sa.Column('clave', sa.String(length=40), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('puntos', sa.Integer(), nullable=False),
    sa.Column('tope_diario', sa.Integer(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('clave')
    )
    niveles = op.create_table('niveles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=60), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('icono', sa.String(length=30), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('xp_minima', sa.Integer(), nullable=False),
    sa.Column('insignias_minimas', sa.Integer(), nullable=False),
    sa.Column('insignias_requeridas', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.create_table('movimientos_xp',
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('accion', sa.String(length=40), nullable=False),
    sa.Column('puntos', sa.Integer(), nullable=False),
    sa.Column('detalle', sa.Text(), nullable=False),
    sa.Column('referencia', sa.String(length=120), nullable=True),
    sa.Column('otorgado_por_id', sa.Uuid(), nullable=True),
    sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['otorgado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('usuario_id', 'accion', 'referencia', name='uq_movimiento_xp_referencia')
    )
    op.create_index('ix_movimientos_xp_creado_en', 'movimientos_xp', ['creado_en'], unique=False)
    op.create_index('ix_movimientos_xp_usuario_id_creado_en', 'movimientos_xp', ['usuario_id', 'creado_en'], unique=False)
    op.create_table('evidencias',
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('proyecto_id', sa.Uuid(), nullable=True),
    sa.Column('titulo', sa.String(length=200), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('tipo', sa.Enum('certificado', 'constancia', 'informe', 'foto', 'otro', name='tipoevidencia', native_enum=False), nullable=False),
    sa.Column('archivo_nombre', sa.String(length=255), nullable=False),
    sa.Column('archivo_ruta', sa.String(length=255), nullable=False),
    sa.Column('archivo_tipo', sa.String(length=100), nullable=False),
    sa.Column('archivo_tamano', sa.Integer(), nullable=False),
    sa.Column('estado', sa.Enum('pendiente', 'aprobada', 'rechazada', name='estadoevidencia', native_enum=False), nullable=False),
    sa.Column('xp_otorgada', sa.Integer(), nullable=False),
    sa.Column('comentario', sa.Text(), nullable=False),
    sa.Column('revisada_por_id', sa.Uuid(), nullable=True),
    sa.Column('revisada_en', sa.DateTime(timezone=True), nullable=True),
    sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['revisada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidencias_creado_en'), 'evidencias', ['creado_en'], unique=False)
    op.create_index(op.f('ix_evidencias_estado'), 'evidencias', ['estado'], unique=False)
    op.create_index(op.f('ix_evidencias_proyecto_id'), 'evidencias', ['proyecto_id'], unique=False)
    op.create_index(op.f('ix_evidencias_usuario_id'), 'evidencias', ['usuario_id'], unique=False)
    op.create_table('postulaciones',
    sa.Column('oportunidad_id', sa.Uuid(), nullable=False),
    sa.Column('proyecto_id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=True),
    sa.Column('estado', sa.Enum('enviada', 'aceptada', 'no_seleccionada', 'retirada', name='estadopostulacion', native_enum=False), nullable=False),
    sa.Column('nota', sa.Text(), nullable=False),
    sa.Column('comentario', sa.Text(), nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('decidida_en', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['oportunidad_id'], ['oportunidades.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('oportunidad_id', 'proyecto_id', name='uq_postulacion_oportunidad_proyecto')
    )
    op.create_index(op.f('ix_postulaciones_estado'), 'postulaciones', ['estado'], unique=False)
    op.create_index(op.f('ix_postulaciones_oportunidad_id'), 'postulaciones', ['oportunidad_id'], unique=False)
    op.create_index(op.f('ix_postulaciones_proyecto_id'), 'postulaciones', ['proyecto_id'], unique=False)
    op.add_column('usuarios', sa.Column('xp', sa.Integer(), server_default='0', nullable=False))
    op.add_column('usuarios', sa.Column('nivel_id', sa.Integer(), nullable=True))
    op.create_foreign_key('usuarios_nivel_id_fkey', 'usuarios', 'niveles', ['nivel_id'], ['id'], ondelete='SET NULL')

    op.bulk_insert(acciones, [
        {'clave': c, 'nombre': n, 'descripcion': d, 'puntos': p, 'tope_diario': t, 'activo': True, 'orden': i}
        for i, (c, n, d, p, t) in enumerate(ACCIONES)])
    op.bulk_insert(niveles, [
        {'nombre': n, 'descripcion': d, 'icono': i, 'color': c, 'xp_minima': x, 'insignias_minimas': m, 'insignias_requeridas': []}
        for n, d, i, c, x, m in NIVELES])
    # Todas las cuentas existentes arrancan en el primer nivel (0 XP).
    op.execute("UPDATE usuarios SET nivel_id = (SELECT id FROM niveles WHERE nombre = 'Novato')")

    conn = op.get_bind()
    for fila in conn.execute(sa.select(_roles.c.clave, _roles.c.permisos).where(_roles.c.clave.in_(ROLES_BASE))).all():
        permisos = _permisos(fila.permisos)
        nuevos = permisos + [p for p in PERMISOS_NUEVOS if p not in permisos]
        conn.execute(_roles.update().where(_roles.c.clave == fila.clave).values(permisos=nuevos))


def downgrade() -> None:
    conn = op.get_bind()
    quitar = PERMISOS_NUEVOS + ["admin.experiencia", "admin.evidencias"]
    for fila in conn.execute(sa.select(_roles.c.clave, _roles.c.permisos)).all():
        permisos = _permisos(fila.permisos)
        if any(p in permisos for p in quitar):
            conn.execute(_roles.update().where(_roles.c.clave == fila.clave).values(permisos=[p for p in permisos if p not in quitar]))
    op.drop_constraint('usuarios_nivel_id_fkey', 'usuarios', type_='foreignkey')
    op.drop_column('usuarios', 'nivel_id')
    op.drop_column('usuarios', 'xp')
    op.drop_index(op.f('ix_postulaciones_proyecto_id'), table_name='postulaciones')
    op.drop_index(op.f('ix_postulaciones_oportunidad_id'), table_name='postulaciones')
    op.drop_index(op.f('ix_postulaciones_estado'), table_name='postulaciones')
    op.drop_table('postulaciones')
    op.drop_index(op.f('ix_evidencias_usuario_id'), table_name='evidencias')
    op.drop_index(op.f('ix_evidencias_proyecto_id'), table_name='evidencias')
    op.drop_index(op.f('ix_evidencias_estado'), table_name='evidencias')
    op.drop_index(op.f('ix_evidencias_creado_en'), table_name='evidencias')
    op.drop_table('evidencias')
    op.drop_index('ix_movimientos_xp_usuario_id_creado_en', table_name='movimientos_xp')
    op.drop_index('ix_movimientos_xp_creado_en', table_name='movimientos_xp')
    op.drop_table('movimientos_xp')
    op.drop_table('niveles')
    op.drop_table('acciones_xp')
