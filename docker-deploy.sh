#!/bin/bash

# Скрипт для развертывания проекта через Docker

set -e

echo "🚀 Развертывание HR Bot..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📝 Создайте .env файл на основе .env.example:"
    echo "   cp .env.example .env"
    echo "   nano .env"
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

# Останавливаем старые контейнеры
echo "🛑 Останавливаем старые контейнеры..."
docker-compose down

# Собираем образы
echo "🔨 Собираем Docker образы..."
docker-compose build --no-cache

# Запускаем контейнеры
echo "▶️  Запускаем сервисы..."
docker-compose up -d

# Показываем статус
echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📊 Статус сервисов:"
docker-compose ps
echo ""
echo "🔗 Доступные сервисы:"
echo "   - API: http://localhost:8000"
echo "   - Webapp: http://localhost:3001"
echo ""
echo "📝 Просмотр логов:"
echo "   - Все сервисы: docker-compose logs -f"
echo "   - Бот: docker-compose logs -f bot"
echo "   - API: docker-compose logs -f api"
echo "   - Webapp: docker-compose logs -f webapp"
echo ""
echo "🛑 Остановка: docker-compose down"
