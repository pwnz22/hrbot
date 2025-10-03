#!/bin/bash

# Скрипт для перезапуска сервисов

SERVICE=${1:-all}

echo "🔄 Перезапуск $SERVICE..."

if [ "$SERVICE" = "all" ]; then
    docker-compose restart
else
    docker-compose restart $SERVICE
fi

echo "✅ Перезапуск завершен!"
docker-compose ps
