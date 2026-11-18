"""fecha de apertura en oportunidades (Ep6-Hu1)

Revision ID: 0014
Revises: 0013
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0014'
down_revision: Union[str, None] = '0013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('oportunidades', sa.Column('abre_en', sa.Date(), server_default=sa.text('CURRENT_DATE'), nullable=False))
    op.create_index(op.f('ix_oportunidades_abre_en'), 'oportunidades', ['abre_en'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_oportunidades_abre_en'), table_name='oportunidades')
    op.drop_column('oportunidades', 'abre_en')
