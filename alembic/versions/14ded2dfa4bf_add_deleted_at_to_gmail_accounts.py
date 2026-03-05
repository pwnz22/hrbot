"""add deleted_at to gmail_accounts

Revision ID: 14ded2dfa4bf
Revises: 8aaaa227e03e
Create Date: 2026-03-05 10:39:10.574046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '14ded2dfa4bf'
down_revision: Union[str, None] = '8aaaa227e03e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
