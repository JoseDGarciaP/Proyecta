"""roles con permisos editables, roles personalizados e insignias

Revision ID: 0008
Revises: 0007
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.modules.roles.seed import ROLES


# Insignias iniciales tal como eran en esta versión (0009 las pasa al formato de reglas).
INSIGNIAS = [
    ("Primer proyecto", "Registró su primer proyecto en la plataforma.", "rocket", "brand", "proyectos_registrados", 1),
    ("Emprendedor/a", "Ha registrado 3 proyectos.", "lightbulb", "amber", "proyectos_registrados", 3),
    ("Colaborador/a", "Se sumó a su primer proyecto de otro equipo.", "handshake", "accent", "colaboraciones", 1),
    ("Aliado/a constante", "Colabora en 5 proyectos de otros equipos.", "users", "violet", "colaboraciones", 5),
    ("Líder de equipo", "Sumó 3 personas a sus proyectos.", "flag", "emerald", "integrantes_sumados", 3),
    ("Proyecto cumplido", "Participó en un proyecto que llegó a «Finalizado».", "trophy", "amber", "proyectos_finalizados", 1),
    ("Perfil completo", "Completó su perfil: descripción, habilidades e intereses.", "badge_check", "sky", "perfil_completo", 1),
    ("Conversador/a", "Envió 50 mensajes en los chats de sus equipos.", "message", "accent", "mensajes_enviados", 50),
    ("Mención de honor", "Reconocimiento especial por un aporte destacado.", "medal", "rose", None, None),
    ("Mentor/a destacado/a", "Acompañó y guió a otros equipos.", "graduation", "violet", None, None),
    ("Innovación", "Propuso una solución especialmente creativa.", "sparkles", "brand", None, None),
]

revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    roles = op.create_table('roles',
    sa.Column('clave', sa.String(length=40), nullable=False),
    sa.Column('nombre', sa.String(length=80), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('permisos', sa.JSON(), nullable=False),
    sa.Column('institucional', sa.Boolean(), nullable=False),
    sa.Column('registro_publico', sa.Boolean(), nullable=False),
    sa.Column('sistema', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('clave')
    )
    op.bulk_insert(roles, [
        {'clave': c, 'nombre': n, 'descripcion': d, 'institucional': i, 'registro_publico': r, 'permisos': list(p),
         'sistema': True, 'orden': k}
        for k, (c, n, d, i, r, p) in enumerate(ROLES)
    ])
    # El rol pasa de un valor fijo a una referencia a la tabla de roles (las claves no cambian).
    op.alter_column('usuarios', 'rol', existing_type=sa.String(length=14), type_=sa.String(length=40), existing_nullable=False)
    op.create_foreign_key('usuarios_rol_fkey', 'usuarios', 'roles', ['rol'], ['clave'])
    op.create_index(op.f('ix_usuarios_rol'), 'usuarios', ['rol'], unique=False)

    insignias = op.create_table('insignias',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=80), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('icono', sa.String(length=30), nullable=False),
    sa.Column('color', sa.String(length=20), nullable=False),
    sa.Column('criterio', sa.String(length=40), nullable=True),
    sa.Column('umbral', sa.Integer(), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    op.bulk_insert(insignias, [
        {'nombre': n, 'descripcion': d, 'icono': i, 'color': c, 'criterio': k, 'umbral': u, 'activo': True, 'orden': o}
        for o, (n, d, i, c, k, u) in enumerate(INSIGNIAS)
    ])
    op.create_table('usuario_insignias',
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('insignia_id', sa.Integer(), nullable=False),
    sa.Column('motivo', sa.Text(), nullable=False),
    sa.Column('automatica', sa.Boolean(), nullable=False),
    sa.Column('otorgada_por_id', sa.Uuid(), nullable=True),
    sa.Column('otorgada_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('retirada_en', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['insignia_id'], ['insignias.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['otorgada_por_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('usuario_id', 'insignia_id', name='uq_usuario_insignia')
    )
    op.create_index(op.f('ix_usuario_insignias_insignia_id'), 'usuario_insignias', ['insignia_id'], unique=False)
    op.create_index(op.f('ix_usuario_insignias_usuario_id'), 'usuario_insignias', ['usuario_id'], unique=False)
    # Las cuentas existentes reciben las insignias automáticas que ya cumplen la primera vez que
    # el admin pulse «Revisar logros» (o al registrar un proyecto, aprobar una solicitud, etc.).


def downgrade() -> None:
    op.drop_index(op.f('ix_usuario_insignias_usuario_id'), table_name='usuario_insignias')
    op.drop_index(op.f('ix_usuario_insignias_insignia_id'), table_name='usuario_insignias')
    op.drop_table('usuario_insignias')
    op.drop_table('insignias')
    op.drop_index(op.f('ix_usuarios_rol'), table_name='usuarios')
    op.drop_constraint('usuarios_rol_fkey', 'usuarios', type_='foreignkey')
    # Los roles personalizados vuelven a «estudiante» antes de restaurar el valor fijo.
    op.execute("UPDATE usuarios SET rol = 'estudiante' WHERE rol NOT IN "
               "('estudiante', 'docente', 'administrativo', 'aliado', 'admin')")
    op.alter_column('usuarios', 'rol', existing_type=sa.String(length=40), type_=sa.String(length=14), existing_nullable=False)
    op.drop_table('roles')
