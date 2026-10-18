"""fecha de modificación de los mensajes del chat

Revision ID: 0005
Revises: 0004
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Los mensajes que ya existían toman como fecha de modificación la de envío.
    op.add_column('proyecto_mensajes', sa.Column('modificado_en', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE proyecto_mensajes SET modificado_en = COALESCE(editado_en, enviado_en)")
    op.alter_column('proyecto_mensajes', 'modificado_en', nullable=False)
    op.create_index('ix_proyecto_mensajes_proyecto_id_modificado_en', 'proyecto_mensajes', ['proyecto_id', 'modificado_en'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_proyecto_mensajes_proyecto_id_modificado_en', table_name='proyecto_mensajes')
    op.drop_column('proyecto_mensajes', 'modificado_en')
