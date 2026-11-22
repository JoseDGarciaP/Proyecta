"""perfiles de aliados externos con verificación (Ep4-Hu12 a Hu15)

Revision ID: 0017
Revises: 0016
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0017'
down_revision: Union[str, None] = '0016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'perfiles_aliado',
        sa.Column('usuario_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('razon_social', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('tipo', sa.String(length=60), nullable=False, server_default='Otro'),
        sa.Column('documento', sa.String(length=30), nullable=True, unique=True),
        sa.Column('telefono', sa.String(length=30), nullable=False, server_default=''),
        sa.Column('sector', sa.String(length=120), nullable=False, server_default=''),
        sa.Column('sitio_web', sa.String(length=300), nullable=False, server_default=''),
        sa.Column('descripcion', sa.Text(), nullable=False, server_default=''),
        sa.Column('estado', sa.String(length=9), nullable=False, server_default='pendiente'),
        sa.Column('motivo_rechazo', sa.Text(), nullable=False, server_default=''),
        sa.Column('revisado_por_id', sa.Uuid(), sa.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True),
        sa.Column('revisado_en', sa.DateTime(timezone=True), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_perfiles_aliado_estado', 'perfiles_aliado', ['estado'])
    op.create_index('ix_perfiles_aliado_sector', 'perfiles_aliado', ['sector'])
    # Los aliados que ya existían quedan aprobados: siguen entrando como hasta ahora.
    op.execute(
        "INSERT INTO perfiles_aliado (usuario_id, razon_social, estado) "
        "SELECT id, nombre, 'aprobado' FROM usuarios WHERE rol = 'aliado'"
    )


def downgrade() -> None:
    op.drop_index('ix_perfiles_aliado_sector', table_name='perfiles_aliado')
    op.drop_index('ix_perfiles_aliado_estado', table_name='perfiles_aliado')
    op.drop_table('perfiles_aliado')
