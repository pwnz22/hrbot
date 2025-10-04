"""migrate accounts from json to db

Revision ID: bd0215db2c9d
Revises: 372310059e7c
Create Date: 2025-10-05 00:41:31.201533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bd0215db2c9d'
down_revision: Union[str, None] = '372310059e7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Миграция данных из JSON в БД
    import json
    import os

    accounts_config_path = "bot/gmail_accounts.json"

    if os.path.exists(accounts_config_path):
        with open(accounts_config_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)

        # Вставляем аккаунты в БД
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        # Используем движок из alembic контекста
        bind = op.get_bind()

        for account in accounts:
            # Проверяем существует ли уже аккаунт по account_id (был id в JSON)
            result = bind.execute(
                sa.text("SELECT id FROM gmail_accounts WHERE account_id = :account_id"),
                {"account_id": account['id']}
            )

            if not result.fetchone():
                # Вставляем новый аккаунт (id будет автоинкрементный integer)
                # account['id'] из JSON → account_id в БД
                bind.execute(
                    sa.text("""
                        INSERT INTO gmail_accounts (account_id, name, credentials_path, token_path, enabled, user_id)
                        VALUES (:account_id, :name, :credentials_path, :token_path, :enabled, NULL)
                    """),
                    {
                        "account_id": account['id'],  # JSON id → account_id
                        "name": account.get('name', account['id']),
                        "credentials_path": account['credentials_path'],
                        "token_path": account['token_path'],
                        "enabled": account.get('enabled', True)
                    }
                )


def downgrade() -> None:
    # Откатываем - удаляем аккаунты которые были добавлены из JSON
    pass
