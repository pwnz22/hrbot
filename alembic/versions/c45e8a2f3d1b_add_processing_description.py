"""add processing description to applications

Revision ID: c45e8a2f3d1b
Revises: 372310059e7c
Create Date: 2025-10-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c45e8a2f3d1b'
down_revision: Union[str, None] = '372310059e7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add processing_description column to applications table
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('processing_description', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove processing_description column from applications table
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_column('processing_description')
