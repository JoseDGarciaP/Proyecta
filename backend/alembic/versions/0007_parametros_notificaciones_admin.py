"""recomendaciones con formato fijo, motivos de decisión, notificaciones y panel de administración

Revision ID: 0007
Revises: 0006
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.modules.parametros.seed import MOTIVOS, PLANTILLAS, TIPOS_APORTE


revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---- Parámetros que configura el admin ----
    motivos = op.create_table('motivos_decision',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tipo', sa.Enum('aprobacion', 'rechazo', name='tipomotivo', native_enum=False), nullable=False),
    sa.Column('nombre', sa.String(length=150), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('requiere_comentario', sa.Boolean(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_motivos_decision_tipo'), 'motivos_decision', ['tipo'], unique=False)
    tipos = op.create_table('tipos_aporte',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nombre', sa.String(length=120), nullable=False),
    sa.Column('descripcion', sa.Text(), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('nombre')
    )
    plantillas = op.create_table('plantillas_mensaje',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('titulo', sa.String(length=120), nullable=False),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.Column('para', sa.Enum('solicitante', 'responsable', 'todos', name='paraplantilla', native_enum=False), nullable=False),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('orden', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ajustes',
    sa.Column('clave', sa.String(length=80), nullable=False),
    sa.Column('valor', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('clave')
    )
    op.bulk_insert(motivos, [
        {'tipo': t, 'nombre': n, 'descripcion': d, 'requiere_comentario': c, 'activo': True, 'orden': i}
        for i, (t, n, d, c) in enumerate(MOTIVOS)
    ])
    op.bulk_insert(tipos, [
        {'nombre': n, 'descripcion': d, 'activo': True, 'orden': i} for i, (n, d) in enumerate(TIPOS_APORTE)
    ])
    op.bulk_insert(plantillas, [
        {'para': p, 'titulo': t, 'texto': x, 'activo': True, 'orden': i} for i, (p, t, x) in enumerate(PLANTILLAS)
    ])

    # ---- Formato fijo de la solicitud y motivo de la decisión ----
    op.add_column('solicitudes_alianza', sa.Column('tipo_aporte_id', sa.Integer(), nullable=True))
    op.add_column('solicitudes_alianza', sa.Column('rol_propuesto', sa.String(length=120), server_default='', nullable=False))
    op.add_column('solicitudes_alianza', sa.Column('aporte', sa.Text(), server_default='', nullable=False))
    op.add_column('solicitudes_alianza', sa.Column('habilidades', sa.JSON(), server_default=sa.text("'[]'"), nullable=False))
    op.add_column('solicitudes_alianza', sa.Column('disponibilidad_horas', sa.SmallInteger(), nullable=True))
    op.add_column('solicitudes_alianza', sa.Column('motivacion', sa.Text(), server_default='', nullable=False))
    op.add_column('solicitudes_alianza', sa.Column('motivo_id', sa.Integer(), nullable=True))
    op.add_column('solicitudes_alianza', sa.Column('motivo_nombre', sa.String(length=150), server_default='', nullable=False))
    op.create_foreign_key('solicitudes_alianza_tipo_aporte_id_fkey', 'solicitudes_alianza', 'tipos_aporte',
                          ['tipo_aporte_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('solicitudes_alianza_motivo_id_fkey', 'solicitudes_alianza', 'motivos_decision',
                          ['motivo_id'], ['id'], ondelete='SET NULL')

    # ---- Preferencias de correo ----
    op.add_column('usuarios', sa.Column(
        'correo_avisos', sa.JSON(),
        server_default=sa.text('\'{"solicitudes": true, "respuestas": true, "mensajes": true}\''), nullable=False))
    op.add_column('usuarios', sa.Column('resumen_hasta', sa.DateTime(timezone=True), nullable=True))

    # ---- Notificaciones (campana) ----
    op.create_table('notificaciones',
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('tipo', sa.Enum('solicitud_nueva', 'invitacion_nueva', 'solicitud_aceptada', 'solicitud_rechazada',
                              'solicitud_cancelada', 'mensajes_sin_leer', 'cuenta', 'moderacion',
                              name='tiponotificacion', native_enum=False), nullable=False),
    sa.Column('titulo', sa.String(length=200), nullable=False),
    sa.Column('cuerpo', sa.Text(), nullable=False),
    sa.Column('enlace', sa.String(length=300), nullable=False),
    sa.Column('leida', sa.Boolean(), nullable=False),
    sa.Column('correo_enviado', sa.Boolean(), nullable=False),
    sa.Column('creada_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notificaciones_leida'), 'notificaciones', ['leida'], unique=False)
    op.create_index('ix_notificaciones_usuario_id_creada_en', 'notificaciones', ['usuario_id', 'creada_en'], unique=False)

    # ---- Bitácora de administración ----
    op.create_table('registro_admin',
    sa.Column('admin_id', sa.Uuid(), nullable=True),
    sa.Column('accion', sa.String(length=80), nullable=False),
    sa.Column('objeto', sa.String(length=250), nullable=False),
    sa.Column('detalle', sa.Text(), nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['admin_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_registro_admin_admin_id'), 'registro_admin', ['admin_id'], unique=False)
    op.create_index(op.f('ix_registro_admin_creado_en'), 'registro_admin', ['creado_en'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_registro_admin_creado_en'), table_name='registro_admin')
    op.drop_index(op.f('ix_registro_admin_admin_id'), table_name='registro_admin')
    op.drop_table('registro_admin')
    op.drop_index('ix_notificaciones_usuario_id_creada_en', table_name='notificaciones')
    op.drop_index(op.f('ix_notificaciones_leida'), table_name='notificaciones')
    op.drop_table('notificaciones')
    op.drop_column('usuarios', 'resumen_hasta')
    op.drop_column('usuarios', 'correo_avisos')
    op.drop_constraint('solicitudes_alianza_motivo_id_fkey', 'solicitudes_alianza', type_='foreignkey')
    op.drop_constraint('solicitudes_alianza_tipo_aporte_id_fkey', 'solicitudes_alianza', type_='foreignkey')
    for columna in ('motivo_nombre', 'motivo_id', 'motivacion', 'disponibilidad_horas', 'habilidades', 'aporte',
                    'rol_propuesto', 'tipo_aporte_id'):
        op.drop_column('solicitudes_alianza', columna)
    op.drop_table('ajustes')
    op.drop_table('plantillas_mensaje')
    op.drop_table('tipos_aporte')
    op.drop_index(op.f('ix_motivos_decision_tipo'), table_name='motivos_decision')
    op.drop_table('motivos_decision')
