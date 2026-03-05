"""add telegram application support

Revision ID: f9e8b7a6c5d4
Revises: e8b4f7a9c2d3
Create Date: 2026-03-05 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'f9e8b7a6c5d4'
down_revision = 'e8b4f7a9c2d3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.alter_column('gmail_message_id',
                   existing_type=sa.String(255),
                   nullable=True)
        batch_op.add_column(sa.Column('application_source', sa.String(50), nullable=True, server_default='email'))

    op.add_column('vacancies', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.add_column('vacancies', sa.Column('requirements', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('applications', schema=None) as batch_op:
        batch_op.alter_column('gmail_message_id',
                   existing_type=sa.String(255),
                   nullable=False)
        batch_op.drop_column('application_source')

    op.drop_column('vacancies', 'is_active')
    op.drop_column('vacancies', 'requirements')
