"""Add Generic pass barcode fields

Revision ID: 3f1a0a0d7e8c
Revises: 26b2a1fa2259
Create Date: 2026-03-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3f1a0a0d7e8c"
down_revision: Union[str, Sequence[str], None] = "26b2a1fa2259"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("Generic_Fields", sa.Column("barcode_type", sa.String(length=100), nullable=True))
    op.add_column("Generic_Fields", sa.Column("barcode_value", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("Generic_Fields", "barcode_value")
    op.drop_column("Generic_Fields", "barcode_type")

