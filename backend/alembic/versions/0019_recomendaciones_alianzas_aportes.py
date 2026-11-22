"""recomendaciones aceptadas/anuladas, valoración del diagnóstico y aportes (Ep5-Hu4 a Hu9, Ep6-Hu9 a Hu11)

Revision ID: 0019
Revises: 0018
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0019'
down_revision: Union[str, None] = '0018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('recomendaciones', sa.Column('motivo', sa.Text(), nullable=False, server_default=''))
    op.add_column('recomendaciones', sa.Column('decidido_por_id', sa.Uuid(),
                                               sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True))
    op.add_column('recomendaciones', sa.Column('decidido_en', sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        'valoraciones_diagnostico',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('proyecto_id', sa.Uuid(), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('util', sa.Boolean(), nullable=False),
        sa.Column('comentario', sa.Text(), nullable=False, server_default=''),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_valoraciones_diagnostico_proyecto_id', 'valoraciones_diagnostico', ['proyecto_id'])

    op.create_table(
        'aportes',
        sa.Column('id', sa.Uuid(), primary_key=True),
        sa.Column('proyecto_id', sa.Uuid(), sa.ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('usuario_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('tipo', sa.String(120), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('horas', sa.Integer(), nullable=True),
        sa.Column('valor', sa.Integer(), nullable=True),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('estado', sa.String(9), nullable=False, server_default='pendiente'),
        sa.Column('comentario', sa.Text(), nullable=False, server_default=''),
        sa.Column('validado_por_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('validado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_aportes_proyecto_id', 'aportes', ['proyecto_id'])
    op.create_index('ix_aportes_usuario_id', 'aportes', ['usuario_id'])
    op.create_index('ix_aportes_estado', 'aportes', ['estado'])


def downgrade() -> None:
    op.drop_table('aportes')
    op.drop_table('valoraciones_diagnostico')
    op.drop_column('recomendaciones', 'decidido_en')
    op.drop_column('recomendaciones', 'decidido_por_id')
    op.drop_column('recomendaciones', 'motivo')
