"""proyectos: problema, objetivos, varias áreas, archivo, historial, adjuntos y observaciones (Ep4-Hu17 a Hu23)

Revision ID: 0018
Revises: 0017
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0018'
down_revision: Union[str, None] = '0017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('proyectos', sa.Column('problema', sa.Text(), nullable=False, server_default=''))
    op.add_column('proyectos', sa.Column('objetivos', sa.Text(), nullable=False, server_default=''))
    op.add_column('proyectos', sa.Column('archivado', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('proyectos', sa.Column('archivado_motivo', sa.Text(), nullable=False, server_default=''))
    op.create_index('ix_proyectos_archivado', 'proyectos', ['archivado'])

    op.create_table(
        'proyecto_areas',
        sa.Column('proyecto_id', sa.Uuid(), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('area_id', sa.Integer(), sa.ForeignKey('areas.id', ondelete='CASCADE'), primary_key=True),
    )
    op.create_table(
        'proyecto_cambios',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('proyecto_id', sa.Uuid(), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('autor_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cambios', sa.JSON(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_proyecto_cambios_proyecto_id', 'proyecto_cambios', ['proyecto_id'])
    op.create_table(
        'proyecto_adjuntos',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('proyecto_id', sa.Uuid(), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subido_por_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('ruta', sa.String(length=255), nullable=False),
        sa.Column('tipo', sa.String(length=100), nullable=False),
        sa.Column('tamano', sa.BigInteger(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_proyecto_adjuntos_proyecto_id', 'proyecto_adjuntos', ['proyecto_id'])
    op.create_table(
        'observaciones',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('proyecto_id', sa.Uuid(), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('autor_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('oculta', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('motivo_oculta', sa.Text(), nullable=False, server_default=''),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('editado_en', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_observaciones_proyecto_id', 'observaciones', ['proyecto_id'])
    op.create_index('ix_observaciones_autor_id', 'observaciones', ['autor_id'])
    op.create_index('ix_observaciones_oculta', 'observaciones', ['oculta'])


def downgrade() -> None:
    op.drop_table('observaciones')
    op.drop_table('proyecto_adjuntos')
    op.drop_table('proyecto_cambios')
    op.drop_table('proyecto_areas')
    op.drop_index('ix_proyectos_archivado', table_name='proyectos')
    for columna in ('archivado_motivo', 'archivado', 'objetivos', 'problema'):
        op.drop_column('proyectos', columna)
