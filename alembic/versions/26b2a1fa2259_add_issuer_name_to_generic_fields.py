"""add_issuer_name_to_generic_fields

Revision ID: 26b2a1fa2259
Revises: 2b73c73a893d
Create Date: 2026-03-19 11:33:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '26b2a1fa2259'
down_revision: Union[str, Sequence[str], None] = '2b73c73a893d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add issuer_name column to Generic_Fields."""
    op.add_column('Generic_Fields', sa.Column('issuer_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Remove issuer_name column from Generic_Fields."""
    op.drop_column('Generic_Fields', 'issuer_name')
