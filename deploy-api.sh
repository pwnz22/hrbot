#!/bin/bash

# Скрипт для развертывания ТОЛЬКО API

set -e

echo "🔌 Развертывание FastAPI..."

if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

docker-compose -f docker-compose.api.yml down
docker-compose -f docker-compose.api.yml build
docker-compose -f docker-compose.api.yml up -d

echo ""
echo "✅ API успешно развернут!"
echo "🔗 API: http://localhost:8000"
echo "📚 Swagger: http://localhost:8000/docs"
echo ""
echo "📝 Логи: docker-compose -f docker-compose.api.yml logs -f"
