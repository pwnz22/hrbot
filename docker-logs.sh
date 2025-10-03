#!/bin/bash

# Скрипт для просмотра логов

SERVICE=${1:-all}

case $SERVICE in
  bot)
    echo "📱 Логи Telegram бота:"
    docker-compose logs -f bot
    ;;
  api)
    echo "🔌 Логи API:"
    docker-compose logs -f api
    ;;
  webapp)
    echo "🌐 Логи Webapp:"
    docker-compose logs -f webapp
    ;;
  all|*)
    echo "📊 Логи всех сервисов:"
    docker-compose logs -f
    ;;
esac
