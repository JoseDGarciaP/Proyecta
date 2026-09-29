"""verificación de correo e ingreso con Google

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Las cuentas que ya existían quedan verificadas; las nuevas empiezan sin verificar.
    op.add_column('usuarios', sa.Column('verificado', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.alter_column('usuarios', 'verificado', server_default=None)
    op.add_column('usuarios', sa.Column('google_sub', sa.String(length=64), nullable=True))
    op.create_unique_constraint('uq_usuarios_google_sub', 'usuarios', ['google_sub'])


def downgrade() -> None:
    op.drop_constraint('uq_usuarios_google_sub', 'usuarios', type_='unique')
    op.drop_column('usuarios', 'google_sub')
    op.drop_column('usuarios', 'verificado')
