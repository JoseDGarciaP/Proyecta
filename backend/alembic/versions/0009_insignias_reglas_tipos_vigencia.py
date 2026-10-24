"""insignias con varios requisitos, tipo (logro, condecoración, reconocimiento), entidad y vigencia

Revision ID: 0009
Revises: 0008
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tipo de las insignias manuales que venían de 0008.
TIPO_INICIAL = {"Mención de honor": "condecoracion", "Mentor/a destacado/a": "reconocimiento", "Innovación": "reconocimiento"}


def upgrade() -> None:
    op.add_column('insignias', sa.Column('tipo', sa.String(length=20), server_default='logro', nullable=False))
    op.add_column('insignias', sa.Column('entidad', sa.String(length=150), server_default='', nullable=False))
    op.add_column('insignias', sa.Column('reglas', sa.JSON(), nullable=True))
    op.add_column('insignias', sa.Column('vence_en', sa.Date(), nullable=True))
    op.add_column('insignias', sa.Column('vigencia_dias', sa.Integer(), nullable=True))
    op.add_column('usuario_insignias', sa.Column('fecha_evento', sa.Date(), nullable=True))
    op.add_column('usuario_insignias', sa.Column('vence_en', sa.DateTime(timezone=True), nullable=True))

    # Un requisito (criterio + umbral) pasa a ser una regla de una sola condición.
    conn = op.get_bind()
    insignias = sa.table('insignias', sa.column('id', sa.Integer), sa.column('nombre', sa.String),
                         sa.column('criterio', sa.String), sa.column('umbral', sa.Integer),
                         sa.column('reglas', sa.JSON), sa.column('tipo', sa.String))
    for fila in conn.execute(sa.select(insignias.c.id, insignias.c.nombre, insignias.c.criterio, insignias.c.umbral)).all():
        reglas = {"modo": "todas", "condiciones": [{"criterio": fila.criterio, "umbral": fila.umbral or 1, "valor": None}]} if fila.criterio else None
        tipo = "logro" if fila.criterio else TIPO_INICIAL.get(fila.nombre, "reconocimiento")
        conn.execute(insignias.update().where(insignias.c.id == fila.id).values(reglas=reglas if reglas else sa.null(), tipo=tipo))
    op.drop_column('insignias', 'umbral')
    op.drop_column('insignias', 'criterio')


def downgrade() -> None:
    op.add_column('insignias', sa.Column('criterio', sa.String(length=40), nullable=True))
    op.add_column('insignias', sa.Column('umbral', sa.Integer(), nullable=True))
    conn = op.get_bind()
    insignias = sa.table('insignias', sa.column('id', sa.Integer), sa.column('criterio', sa.String),
                         sa.column('umbral', sa.Integer), sa.column('reglas', sa.JSON))
    for fila in conn.execute(sa.select(insignias.c.id, insignias.c.reglas)).all():
        reglas = fila.reglas if isinstance(fila.reglas, dict) else json.loads(fila.reglas or "null")
        primera = (reglas or {}).get("condiciones", [None])[0] if reglas else None
        if primera:  # solo se conserva el primer requisito
            conn.execute(insignias.update().where(insignias.c.id == fila.id).values(criterio=primera["criterio"], umbral=primera["umbral"]))
    op.drop_column('usuario_insignias', 'vence_en')
    op.drop_column('usuario_insignias', 'fecha_evento')
    op.drop_column('insignias', 'vigencia_dias')
    op.drop_column('insignias', 'vence_en')
    op.drop_column('insignias', 'reglas')
    op.drop_column('insignias', 'entidad')
    op.drop_column('insignias', 'tipo')
