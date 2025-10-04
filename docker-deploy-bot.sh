#!/bin/bash

# Скрипт для развертывания только Telegram бота

echo "🚀 Развертывание Telegram бота..."
echo ""

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте .env файл на основе .env.example"
    exit 1
fi

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p downloads exports logs gmail_tokens bot

# Создание файла базы данных если не существует
if [ ! -f hrbot.db ]; then
    echo "💾 Создание файла базы данных..."
    touch hrbot.db
    chmod 666 hrbot.db
fi

# Создание конфига Gmail аккаунтов если не существует
if [ ! -f bot/gmail_accounts.json ]; then
    echo "📧 Создание конфигурации Gmail аккаунтов..."
    echo '[]' > bot/gmail_accounts.json
    chmod 666 bot/gmail_accounts.json
fi

# Проверка наличия gmail_tokens/credentials.json
if [ ! -f gmail_tokens/credentials.json ]; then
    echo "⚠️  ВНИМАНИЕ: gmail_tokens/credentials.json не найден!"
    echo "Для работы с Gmail нужно добавить credentials.json"
    echo "Инструкция: см. GMAIL_ACCOUNTS_SETUP.md"
    echo ""
fi

# Остановка существующего контейнера
echo "🛑 Остановка существующего контейнера..."
docker-compose stop bot 2>/dev/null

# Пересборка образа
echo "🔨 Пересборка Docker образа..."
docker-compose build bot

# Запуск контейнера
echo "▶️  Запуск Telegram бота..."
docker-compose up -d bot

# Ожидание запуска
echo ""
echo "⏳ Ожидание запуска (5 сек)..."
sleep 5

# Проверка статуса
echo ""
echo "📊 Статус контейнера:"
docker-compose ps bot

echo ""
echo "📋 Последние логи:"
docker-compose logs --tail=20 bot

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "Полезные команды:"
echo "  Логи:        docker-compose logs -f bot"
echo "  Перезапуск:  docker-compose restart bot"
echo "  Остановка:   docker-compose stop bot"
echo "  Статус:      docker-compose ps bot"
echo ""
