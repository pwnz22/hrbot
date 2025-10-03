#!/bin/bash

# Скрипт для развертывания ТОЛЬКО webapp

set -e

echo "🌐 Развертывание Vue.js приложения..."

docker-compose -f docker-compose.webapp.yml down
docker-compose -f docker-compose.webapp.yml build
docker-compose -f docker-compose.webapp.yml up -d

echo ""
echo "✅ Webapp успешно развернут!"
echo "🔗 URL: http://localhost:3001"
echo ""
echo "📝 Логи: docker-compose -f docker-compose.webapp.yml logs -f"
