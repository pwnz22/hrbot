#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления поддержки Gmail аккаунтов
"""
import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect('hrbot.db')
        cursor = conn.cursor()

        print("🔄 Начало миграции базы данных...")

        # Создаем таблицу gmail_accounts если её нет
        print("   Создание таблицы gmail_accounts...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gmail_accounts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                credentials_path TEXT NOT NULL,
                token_path TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                user_id INTEGER REFERENCES telegram_users(id)
            )
        """)

        # Проверяем есть ли колонка gmail_account_id в vacancies
        cursor.execute("PRAGMA table_info(vacancies)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'gmail_account_id' not in columns:
            print("   Добавление колонки gmail_account_id в vacancies...")
            cursor.execute("""
                ALTER TABLE vacancies
                ADD COLUMN gmail_account_id TEXT REFERENCES gmail_accounts(id)
            """)
        else:
            print("   Колонка gmail_account_id уже существует")

        conn.commit()
        print("✅ Миграция завершена успешно!")

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
