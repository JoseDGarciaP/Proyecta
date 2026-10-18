"""chat de proyectos

Revision ID: 0004
Revises: 0003
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('proyecto_mensajes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('proyecto_id', sa.Uuid(), nullable=False),
    sa.Column('autor_id', sa.Uuid(), nullable=True),
    sa.Column('texto', sa.Text(), nullable=False),
    sa.Column('enviado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('editado_en', sa.DateTime(timezone=True), nullable=True),
    sa.Column('eliminado', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['autor_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_proyecto_mensajes_autor_id'), 'proyecto_mensajes', ['autor_id'], unique=False)
    op.create_index('ix_proyecto_mensajes_proyecto_id_id', 'proyecto_mensajes', ['proyecto_id', 'id'], unique=False)
    op.create_table('proyecto_chat_lecturas',
    sa.Column('proyecto_id', sa.Uuid(), nullable=False),
    sa.Column('usuario_id', sa.Uuid(), nullable=False),
    sa.Column('ultimo_leido_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('proyecto_id', 'usuario_id')
    )


def downgrade() -> None:
    op.drop_table('proyecto_chat_lecturas')
    op.drop_index('ix_proyecto_mensajes_proyecto_id_id', table_name='proyecto_mensajes')
    op.drop_index(op.f('ix_proyecto_mensajes_autor_id'), table_name='proyecto_mensajes')
    op.drop_table('proyecto_mensajes')
