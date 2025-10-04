"""remove file_url from applications

Revision ID: 372310059e7c
Revises: b5d95e330be9
Create Date: 2025-10-05 00:03:01.460723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '372310059e7c'
down_revision: Union[str, None] = 'b5d95e330be9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove file_url column from applications table
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.drop_column('file_url')


def downgrade() -> None:
    # Add file_url column back
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_url', sa.String(500), nullable=True))
