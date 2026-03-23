"""rename issuer_name to card_title in generic_fields

Revision ID: d7b0b6b636e3
Revises: 3f1a0a0d7e8c
Create Date: 2026-03-23 09:50:18.418374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7b0b6b636e3'
down_revision: Union[str, Sequence[str], None] = '3f1a0a0d7e8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('Generic_Fields', 'issuer_name', new_column_name='card_title', existing_type=sa.String(length=255))

def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('Generic_Fields', 'card_title', new_column_name='issuer_name', existing_type=sa.String(length=255))
