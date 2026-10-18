"""conversación en solicitudes e invitaciones

Revision ID: 0006
Revises: 0005
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('solicitud_mensajes',
    sa.Column('solicitud_id', sa.Uuid(), nullable=False),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('autor_id', sa.Uuid(), nullable=True),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.Column('enviado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('editado_en', sa.DateTime(timezone=True), nullable=True),
    sa.Column('eliminado', sa.Boolean(), nullable=False),
    sa.Column('modificado_en', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['autor_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes_alianza.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_solicitud_mensajes_autor_id'), 'solicitud_mensajes', ['autor_id'], unique=False)
    op.create_index('ix_solicitud_mensajes_solicitud_id_id', 'solicitud_mensajes', ['solicitud_id', 'id'], unique=False)
    op.create_index('ix_solicitud_mensajes_solicitud_id_modificado_en', 'solicitud_mensajes', ['solicitud_id', 'modificado_en'], unique=False)
    op.create_table('solicitud_chat_lecturas',
    sa.Column('solicitud_id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('ultimo_leido_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes_alianza.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('solicitud_id', 'usuario_id')
    )


def downgrade() -> None:
    op.drop_table('solicitud_chat_lecturas')
    op.drop_index('ix_solicitud_mensajes_solicitud_id_modificado_en', table_name='solicitud_mensajes')
    op.drop_index('ix_solicitud_mensajes_solicitud_id_id', table_name='solicitud_mensajes')
    op.drop_index(op.f('ix_solicitud_mensajes_autor_id'), table_name='solicitud_mensajes')
    op.drop_table('solicitud_mensajes')
