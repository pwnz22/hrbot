"""add source and telegram_user_id to applications, make gmail_message_id nullable

Revision ID: e7f1a2b3c4d5
Revises: a1b2c3d4e5f6
Create Date: 2026-04-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7f1a2b3c4d5'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(length=20), nullable=False, server_default='gmail'))
        batch_op.add_column(sa.Column('telegram_user_id', sa.BigInteger(), nullable=True))
        batch_op.alter_column('gmail_message_id', existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.alter_column('gmail_message_id', existing_type=sa.String(length=255), nullable=False)
        batch_op.drop_column('telegram_user_id')
        batch_op.drop_column('source')
