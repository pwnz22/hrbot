#!/bin/bash

# Скрипт для развертывания ТОЛЬКО бота

set -e

echo "🤖 Развертывание Telegram бота..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте .env файл на основе .env.example:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Проверяем BOT_TOKEN
if ! grep -q "BOT_TOKEN=.*[^[:space:]]" .env; then
    echo "❌ BOT_TOKEN не настроен в .env файле!"
    exit 1
fi

# Проверяем наличие credentials.json
if [ ! -f credentials.json ]; then
    echo "⚠️  Внимание: credentials.json не найден!"
    echo "   Gmail интеграция не будет работать без этого файла."
    read -p "   Продолжить без Gmail? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Останавливаем старый контейнер
echo "🛑 Останавливаем старый контейнер..."
docker-compose -f docker-compose.bot.yml down

# Собираем образ
echo "🔨 Собираем Docker образ..."
docker-compose -f docker-compose.bot.yml build

# Запускаем контейнер
echo "▶️  Запускаем бота..."
docker-compose -f docker-compose.bot.yml up -d

# Показываем статус
echo ""
echo "✅ Бот успешно развернут!"
echo ""
echo "📊 Статус:"
docker-compose -f docker-compose.bot.yml ps
echo ""
echo "📝 Просмотр логов:"
echo "   docker-compose -f docker-compose.bot.yml logs -f"
echo ""
echo "🛑 Остановка:"
echo "   docker-compose -f docker-compose.bot.yml down"
