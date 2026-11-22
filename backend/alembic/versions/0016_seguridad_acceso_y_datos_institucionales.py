"""seguridad de acceso y datos institucionales (Ep4-Hu1, Hu2, Hu6)

Revision ID: 0016
Revises: 0015
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0016'
down_revision: Union[str, None] = '0015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('codigo', sa.String(length=30), nullable=True))
    op.add_column('usuarios', sa.Column('cedula', sa.String(length=30), nullable=True))
    op.add_column('usuarios', sa.Column('sexo', sa.String(length=20), nullable=True))
    op.add_column('usuarios', sa.Column('acepto_datos_en', sa.DateTime(timezone=True), nullable=True))
    op.add_column('usuarios', sa.Column('intentos_fallidos', sa.Integer(), server_default='0', nullable=False))
    op.add_column('usuarios', sa.Column('bloqueado_hasta', sa.DateTime(timezone=True), nullable=True))
    op.add_column('usuarios', sa.Column('sesion_version', sa.Integer(), server_default='0', nullable=False))
    op.create_unique_constraint('uq_usuarios_codigo', 'usuarios', ['codigo'])
    op.create_unique_constraint('uq_usuarios_cedula', 'usuarios', ['cedula'])


def downgrade() -> None:
    op.drop_constraint('uq_usuarios_cedula', 'usuarios', type_='unique')
    op.drop_constraint('uq_usuarios_codigo', 'usuarios', type_='unique')
    for columna in ('sesion_version', 'bloqueado_hasta', 'intentos_fallidos', 'acepto_datos_en', 'sexo', 'cedula', 'codigo'):
        op.drop_column('usuarios', columna)
