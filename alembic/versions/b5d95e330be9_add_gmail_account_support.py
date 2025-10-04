"""initial database schema

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
    # Create telegram_users table
    op.create_table(
        'telegram_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('last_name', sa.String(255), nullable=True),
        sa.Column('role', sa.Enum('USER', 'MODERATOR', 'ADMIN', name='roleenum'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_telegram_users_id', 'telegram_users', ['id'])
    op.create_index('ix_telegram_users_telegram_id', 'telegram_users', ['telegram_id'], unique=True)

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

    # Create vacancies table
    op.create_table(
        'vacancies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('gmail_account_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['gmail_account_id'], ['gmail_accounts.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('title')
    )
    op.create_index('ix_vacancies_id', 'vacancies', ['id'])

    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_url', sa.String(500), nullable=True),
        sa.Column('attachment_filename', sa.String(255), nullable=True),
        sa.Column('gmail_message_id', sa.String(255), nullable=False),
        sa.Column('applicant_message', sa.Text(), nullable=True),
        sa.Column('vacancy_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['vacancy_id'], ['vacancies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gmail_message_id')
    )
    op.create_index('ix_applications_id', 'applications', ['id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_applications_id', 'applications')
    op.drop_table('applications')

    op.drop_index('ix_vacancies_id', 'vacancies')
    op.drop_table('vacancies')

    op.drop_table('gmail_accounts')

    op.drop_index('ix_telegram_users_telegram_id', 'telegram_users')
    op.drop_index('ix_telegram_users_id', 'telegram_users')
    op.drop_table('telegram_users')
