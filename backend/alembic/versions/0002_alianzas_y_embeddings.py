"""alianzas y embeddings

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27 16:43:08.844081
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('embeddings',
    sa.Column('entidad', sa.String(length=20), nullable=False),
    sa.Column('entidad_id', sa.Uuid(), nullable=False),
    sa.Column('modelo', sa.String(length=200), nullable=False),
    sa.Column('huella', sa.String(length=64), nullable=False),
    sa.Column('vector', Vector(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('entidad', 'entidad_id')
    )
    op.create_table('proyecto_miembros',
    sa.Column('proyecto_id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('rol', sa.String(length=80), nullable=False),
    sa.Column('desde', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('proyecto_id', 'usuario_id')
    )
    op.create_index(op.f('ix_proyecto_miembros_usuario_id'), 'proyecto_miembros', ['usuario_id'], unique=False)
    op.create_table('solicitudes_alianza',
    sa.Column('proyecto_id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('tipo', sa.Enum('solicitud', 'invitacion', name='tiposolicitud', native_enum=False), nullable=False),
    sa.Column('estado', sa.Enum('pendiente', 'aceptada', 'rechazada', 'cancelada', name='estadosolicitud', native_enum=False), nullable=False),
    sa.Column('mensaje', sa.Text(), nullable=False),
    sa.Column('respuesta', sa.Text(), nullable=False),
    sa.Column('respondida_en', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('creado_en', sa.Date(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_solicitudes_alianza_estado'), 'solicitudes_alianza', ['estado'], unique=False)
    op.create_index(op.f('ix_solicitudes_alianza_proyecto_id'), 'solicitudes_alianza', ['proyecto_id'], unique=False)
    op.create_index(op.f('ix_solicitudes_alianza_usuario_id'), 'solicitudes_alianza', ['usuario_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_solicitudes_alianza_usuario_id'), table_name='solicitudes_alianza')
    op.drop_index(op.f('ix_solicitudes_alianza_proyecto_id'), table_name='solicitudes_alianza')
    op.drop_index(op.f('ix_solicitudes_alianza_estado'), table_name='solicitudes_alianza')
    op.drop_table('solicitudes_alianza')
    op.drop_index(op.f('ix_proyecto_miembros_usuario_id'), table_name='proyecto_miembros')
    op.drop_table('proyecto_miembros')
    op.drop_table('embeddings')
