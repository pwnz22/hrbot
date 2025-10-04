"""add gmail account support

Revision ID: b5d95e330be9
Revises: 
Create Date: 2025-10-04 23:07:22.980821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5d95e330be9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create gmail_accounts table
    op.create_table(
        'gmail_accounts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('credentials_path', sa.String(), nullable=False),
        sa.Column('token_path', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['telegram_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add gmail_account_id column to vacancies table
    op.add_column('vacancies', sa.Column('gmail_account_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'vacancies', 'gmail_accounts', ['gmail_account_id'], ['id'])


def downgrade() -> None:
    # Remove gmail_account_id column from vacancies table
    op.drop_constraint(None, 'vacancies', type_='foreignkey')
    op.drop_column('vacancies', 'gmail_account_id')

    # Drop gmail_accounts table
    op.drop_table('gmail_accounts')
