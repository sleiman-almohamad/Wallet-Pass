"""Add generic class text module rows and fields

Revision ID: f7b7d24e9293
Revises: 8b4b16c627fe
Create Date: 2026-03-10 14:34:37.584196

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7b7d24e9293'
down_revision: Union[str, Sequence[str], None] = '8b4b16c627fe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('GenericClass_Fields', sa.Column('multiple_devices_allowed', sa.String(length=100), nullable=True))
    op.add_column('GenericClass_Fields', sa.Column('view_unlock_requirement', sa.String(length=100), nullable=True))
    op.add_column('GenericClass_Fields', sa.Column('enable_smart_tap', sa.Boolean(), nullable=True))
    
    op.create_table('GenericClass_TextModuleRows',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('class_id', sa.String(length=255, collation='utf8mb4_unicode_ci'), nullable=False),
        sa.Column('row_index', sa.Integer(), nullable=False),
        sa.Column('left_header', sa.String(length=255), nullable=True),
        sa.Column('left_body', sa.Text(), nullable=True),
        sa.Column('middle_header', sa.String(length=255), nullable=True),
        sa.Column('middle_body', sa.Text(), nullable=True),
        sa.Column('right_header', sa.String(length=255), nullable=True),
        sa.Column('right_body', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['GenericClass_Fields.class_id'], onupdate='CASCADE', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    op.create_index(op.f('ix_GenericClass_TextModuleRows_class_id'), 'GenericClass_TextModuleRows', ['class_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_GenericClass_TextModuleRows_class_id'), table_name='GenericClass_TextModuleRows')
    op.drop_table('GenericClass_TextModuleRows')
    op.drop_column('GenericClass_Fields', 'enable_smart_tap')
    op.drop_column('GenericClass_Fields', 'view_unlock_requirement')
    op.drop_column('GenericClass_Fields', 'multiple_devices_allowed')
