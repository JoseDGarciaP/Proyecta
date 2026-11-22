"""áreas Seguridad y Seguridad vial (carga por lote del formulario de registro)

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

NUEVAS = ("Seguridad", "Seguridad vial")


def upgrade() -> None:
    # Solo las que falten: el admin pudo haberlas creado ya desde el panel.
    for nombre in NUEVAS:
        op.execute(sa.text("INSERT INTO areas (nombre) SELECT :n WHERE NOT EXISTS (SELECT 1 FROM areas WHERE nombre = :n)")
                   .bindparams(n=nombre))


def downgrade() -> None:
    # No se borran: puede haber proyectos que ya las usan.
    pass
