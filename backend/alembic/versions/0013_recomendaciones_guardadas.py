"""recomendaciones de la IA guardadas con fecha y estado (HU-05)

Revision ID: 0013
Revises: 0012
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0013'
down_revision: Union[str, None] = '0012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('recomendaciones',
    sa.Column('proyecto_id', sa.Uuid(), nullable=False),
    sa.Column('tipo', sa.Enum('oportunidad', 'colaborador', name='tiporecomendacion', native_enum=False), nullable=False),
    sa.Column('objetivo_id', sa.Uuid(), nullable=False),
    sa.Column('titulo', sa.String(length=200), nullable=False),
    sa.Column('puntaje', sa.Float(), nullable=False),
    sa.Column('razon', sa.Text(), nullable=False),
    sa.Column('estado', sa.Enum('pendiente', 'aceptada', 'anulada', name='estadorecomendacion', native_enum=False), nullable=False),
    sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recomendaciones_proyecto_id'), 'recomendaciones', ['proyecto_id'], unique=False)
    op.create_index(op.f('ix_recomendaciones_tipo'), 'recomendaciones', ['tipo'], unique=False)
    op.create_index(op.f('ix_recomendaciones_objetivo_id'), 'recomendaciones', ['objetivo_id'], unique=False)
    op.create_index(op.f('ix_recomendaciones_estado'), 'recomendaciones', ['estado'], unique=False)
    # En Supabase: igual que la migración 0011, la tabla nueva queda cerrada a la API REST automática.
    op.execute("""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
     AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    ALTER TABLE public.recomendaciones ENABLE ROW LEVEL SECURITY;
    REVOKE ALL ON public.recomendaciones FROM anon, authenticated;
  END IF;
END $$;
""")


def downgrade() -> None:
    op.drop_index(op.f('ix_recomendaciones_estado'), table_name='recomendaciones')
    op.drop_index(op.f('ix_recomendaciones_objetivo_id'), table_name='recomendaciones')
    op.drop_index(op.f('ix_recomendaciones_tipo'), table_name='recomendaciones')
    op.drop_index(op.f('ix_recomendaciones_proyecto_id'), table_name='recomendaciones')
    op.drop_table('recomendaciones')
