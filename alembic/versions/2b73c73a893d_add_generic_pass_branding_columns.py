"""add_generic_pass_branding_columns

Revision ID: 2b73c73a893d
Revises: f7b7d24e9293
Create Date: 2026-03-18 13:35:31.933472

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2b73c73a893d'
down_revision: Union[str, Sequence[str], None] = 'f7b7d24e9293'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add per-pass branding columns to Generic_Fields."""
    op.add_column('Generic_Fields', sa.Column('logo_url', sa.Text(), nullable=True))
    op.add_column('Generic_Fields', sa.Column('hero_image_url', sa.Text(), nullable=True))
    op.add_column('Generic_Fields', sa.Column('hex_background_color', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Remove per-pass branding columns from Generic_Fields."""
    op.drop_column('Generic_Fields', 'hex_background_color')
    op.drop_column('Generic_Fields', 'hero_image_url')
    op.drop_column('Generic_Fields', 'logo_url')
