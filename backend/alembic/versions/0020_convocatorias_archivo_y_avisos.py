"""convocatorias archivadas y avisos de cierre, notificaciones archivadas (Ep6-Hu5, Ep6-Hu13, Ep6-Hu15)

Revision ID: 0020
Revises: 0019
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0020'
down_revision: Union[str, None] = '0019'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('oportunidades', sa.Column('archivada', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('oportunidades', sa.Column('aviso_7_dias', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('oportunidades', sa.Column('aviso_1_dia', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index('ix_oportunidades_archivada', 'oportunidades', ['archivada'])
    op.add_column('notificaciones', sa.Column('archivada', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index('ix_notificaciones_archivada', 'notificaciones', ['archivada'])
    # Lo que ya tiene más de 90 días queda archivado de una vez.
    op.execute("UPDATE notificaciones SET archivada = true WHERE creada_en < now() - interval '90 days'")


def downgrade() -> None:
    op.drop_index('ix_notificaciones_archivada', 'notificaciones')
    op.drop_column('notificaciones', 'archivada')
    op.drop_index('ix_oportunidades_archivada', 'oportunidades')
    op.drop_column('oportunidades', 'aviso_1_dia')
    op.drop_column('oportunidades', 'aviso_7_dias')
    op.drop_column('oportunidades', 'archivada')
