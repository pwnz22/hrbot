#!/bin/bash

# Скрипт для полного пересоздания БД через Alembic

echo "🗑️  Удаление старой базы данных..."
rm -f hrbot.db

echo "🗑️  Очистка кэша Alembic..."
rm -rf alembic/versions/__pycache__
rm -f alembic/versions/*.pyc

echo "📝 Создание новой БД через Alembic..."
alembic upgrade head

echo "✅ База данных пересоздана!"
echo ""
echo "Для проверки структуры выполните:"
echo "python -c \"import sqlite3; conn = sqlite3.connect('hrbot.db'); cursor = conn.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\"'); print([row[0] for row in cursor]); conn.close()\""
