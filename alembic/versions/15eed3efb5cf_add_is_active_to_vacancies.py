"""add is_active to vacancies

Revision ID: 15eed3efb5cf
Revises: 14ded2dfa4bf
Create Date: 2026-03-05 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '15eed3efb5cf'
down_revision: Union[str, None] = '14ded2dfa4bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('vacancies', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('vacancies', 'is_active')
