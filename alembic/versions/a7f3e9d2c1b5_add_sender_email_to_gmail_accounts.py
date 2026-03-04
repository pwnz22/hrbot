"""add sender_email to gmail_accounts

Revision ID: a7f3e9d2c1b5
Revises: c45e8a2f3d1b
Create Date: 2025-03-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7f3e9d2c1b5'
down_revision: Union[str, None] = 'c45e8a2f3d1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('gmail_accounts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sender_email', sa.String(), nullable=False, server_default='noreply@somon.tj'))


def downgrade() -> None:
    with op.batch_alter_table('gmail_accounts', schema=None) as batch_op:
        batch_op.drop_column('sender_email')
