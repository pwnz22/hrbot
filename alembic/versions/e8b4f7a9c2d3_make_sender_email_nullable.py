"""make sender_email nullable

Revision ID: e8b4f7a9c2d3
Revises: a7f3e9d2c1b5
Create Date: 2025-03-04 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e8b4f7a9c2d3'
down_revision: Union[str, None] = 'a7f3e9d2c1b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('gmail_accounts', schema=None) as batch_op:
        batch_op.alter_column('sender_email',
                              existing_type=sa.String(),
                              nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('gmail_accounts', schema=None) as batch_op:
        batch_op.alter_column('sender_email',
                              existing_type=sa.String(),
                              nullable=False)
