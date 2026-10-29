"""invitaciones a proyectos por correo para personas que aún no tienen cuenta

Revision ID: 0012
Revises: 0011
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0012'
down_revision: Union[str, None] = '0011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('invitaciones_correo',
    sa.Column('proyecto_id', sa.Uuid(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('invitado_por_id', sa.Uuid(), nullable=True),
    sa.Column('estado', sa.Enum('pendiente', 'aceptada', 'rechazada', 'cancelada', name='estadosolicitud', native_enum=False), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('expira_en', sa.DateTime(timezone=True), nullable=False),
    sa.Column('respondida_en', sa.DateTime(timezone=True), nullable=True),
    sa.Column('solicitud_id', sa.Uuid(), nullable=True),
    sa.Column('tipo_aporte_id', sa.Integer(), nullable=True),
    sa.Column('rol_propuesto', sa.String(length=120), nullable=False),
    sa.Column('aporte', sa.Text(), nullable=False),
    sa.Column('habilidades', sa.JSON(), nullable=False),
    sa.Column('disponibilidad_horas', sa.SmallInteger(), nullable=True),
    sa.Column('motivacion', sa.Text(), nullable=False),
    sa.Column('mensaje', sa.Text(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('creado_en', sa.Date(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['invitado_por_id'], ['usuarios.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes_alianza.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['tipo_aporte_id'], ['tipos_aporte.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_invitaciones_correo_email'), 'invitaciones_correo', ['email'], unique=False)
    op.create_index(op.f('ix_invitaciones_correo_estado'), 'invitaciones_correo', ['estado'], unique=False)
    op.create_index(op.f('ix_invitaciones_correo_proyecto_id'), 'invitaciones_correo', ['proyecto_id'], unique=False)
    # En Supabase: igual que la migración 0011, la tabla nueva queda cerrada a la API REST automática.
    op.execute("""
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon')
     AND EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
    ALTER TABLE public.invitaciones_correo ENABLE ROW LEVEL SECURITY;
    REVOKE ALL ON public.invitaciones_correo FROM anon, authenticated;
  END IF;
END $$;
""")


def downgrade() -> None:
    op.drop_index(op.f('ix_invitaciones_correo_proyecto_id'), table_name='invitaciones_correo')
    op.drop_index(op.f('ix_invitaciones_correo_estado'), table_name='invitaciones_correo')
    op.drop_index(op.f('ix_invitaciones_correo_email'), table_name='invitaciones_correo')
    op.drop_table('invitaciones_correo')
