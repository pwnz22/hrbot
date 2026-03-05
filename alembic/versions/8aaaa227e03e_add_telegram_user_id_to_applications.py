"""add telegram_user_id to applications

Revision ID: 8aaaa227e03e
Revises: f9e8b7a6c5d4
Create Date: 2026-03-05 10:22:11.735106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8aaaa227e03e'
down_revision: Union[str, None] = 'f9e8b7a6c5d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('applications', sa.Column('telegram_user_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('applications', 'telegram_user_id')
