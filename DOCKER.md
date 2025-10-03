# 🐳 Docker Development Guide

Полная инструкция по развертыванию HR Bot с помощью Docker.

## 📋 Требования

- Docker 20.10+
- Docker Compose 2.0+
- Минимум 2GB свободного места

## 🚀 Быстрый старт

### 1. Подготовка окружения

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd hrbot

# Создайте .env файл
cp .env.example .env
nano .env
```

### 2. Настройка переменных окружения (.env)

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///./hrbot.db
GEMINI_API_KEY=your_gemini_api_key
GRPC_VERBOSITY=ERROR
GMAIL_CHECK_INTERVAL=5
```

### 3. Gmail credentials (опционально)

Если нужна интеграция с Gmail:
- Поместите `credentials.json` в корень проекта
- При первом запуске бот попросит авторизацию

### 4. Запуск одной командой

```bash
./docker-deploy.sh
```

Или вручную:
```bash
docker-compose up -d
```

## 📊 Архитектура

Проект состоит из 3 сервисов:

### 1. **bot** - Telegram бот
- Порт: нет (работает через Telegram API)
- Команда: `python -m bot.main`
- Автоматический парсинг Gmail каждые 5 минут

### 2. **api** - FastAPI REST API
- Порт: `8000`
- URL: http://localhost:8000
- Swagger: http://localhost:8000/docs

### 3. **webapp** - Vue.js веб-приложение
- Порт: `3001`
- URL: http://localhost:3001
- Telegram Mini App интерфейс

## 🛠 Управление

### Просмотр логов

```bash
# Все сервисы
./docker-logs.sh

# Только бот
./docker-logs.sh bot

# Только API
./docker-logs.sh api

# Только webapp
./docker-logs.sh webapp
```

Или через docker-compose:
```bash
docker-compose logs -f
docker-compose logs -f bot
docker-compose logs -f api
```

### Перезапуск сервисов

```bash
# Все сервисы
./docker-restart.sh

# Конкретный сервис
./docker-restart.sh bot
./docker-restart.sh api
```

### Остановка

```bash
docker-compose down
```

### Полная пересборка

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📁 Volumes и данные

Следующие директории монтируются в контейнеры:

- `./hrbot.db` - База данных SQLite (shared между bot и api)
- `./downloads/` - Скачанные резюме
- `./exports/` - Экспортированные Excel файлы
- `./logs/` - Логи приложения
- `./credentials.json` - Gmail OAuth credentials (read-only)
- `./token.json` - Gmail токен доступа

## 🔧 Полезные команды

### Выполнить команду в контейнере

```bash
# Зайти в контейнер бота
docker-compose exec bot bash

# Зайти в контейнер API
docker-compose exec api bash

# Выполнить Python команду
docker-compose exec bot python -m bot.main
```

### Просмотр статуса

```bash
docker-compose ps
```

### Просмотр ресурсов

```bash
docker stats
```

### Очистка

```bash
# Остановить и удалить контейнеры
docker-compose down

# + удалить volumes
docker-compose down -v

# + удалить образы
docker-compose down --rmi all
```

## 🌐 Развертывание на сервере

### Вариант 1: Прямое развертывание

```bash
# На сервере
git clone <repository-url>
cd hrbot
cp .env.example .env
nano .env  # настройте переменные

# Добавьте credentials.json если нужно
scp credentials.json user@server:/path/to/hrbot/

# Запустите
./docker-deploy.sh
```

### Вариант 2: CI/CD через GitHub Actions

Создайте `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Server

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /path/to/hrbot
            git pull
            ./docker-deploy.sh
```

### Вариант 3: С Nginx reverse proxy

Создайте `/etc/nginx/sites-available/hrbot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 Безопасность

### Важные замечания:

1. **Никогда** не коммитьте `.env` в git
2. **Никогда** не коммитьте `credentials.json` и `token.json`
3. Используйте секреты для CI/CD
4. На production используйте SSL/TLS (Let's Encrypt)
5. Ограничьте доступ к портам через firewall

### Рекомендуемые настройки firewall:

```bash
# Разрешить только SSH и HTTP/HTTPS
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

## 🐛 Troubleshooting

### Бот не запускается

```bash
# Проверьте логи
docker-compose logs bot

# Проверьте переменные окружения
docker-compose exec bot env | grep BOT_TOKEN

# Перезапустите
docker-compose restart bot
```

### API не отвечает

```bash
# Проверьте запущен ли контейнер
docker-compose ps api

# Проверьте порт
curl http://localhost:8000

# Проверьте логи
docker-compose logs api
```

### База данных не доступна

```bash
# Проверьте права на файл
ls -la hrbot.db

# Проверьте volume
docker-compose exec bot ls -la /app/hrbot.db
docker-compose exec api ls -la /app/hrbot.db
```

### Gmail интеграция не работает

```bash
# Проверьте наличие credentials.json
docker-compose exec bot ls -la /app/credentials.json

# Проверьте token.json
docker-compose exec bot cat /app/token.json

# Пересоздайте токен (удалите и перезапустите)
rm token.json
docker-compose restart bot
```

## 📈 Мониторинг

### Prometheus + Grafana (опционально)

Добавьте в `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

## 💡 Советы

1. Используйте `docker-compose logs -f` для real-time мониторинга
2. Регулярно делайте бэкапы `hrbot.db`
3. Обновляйте образы: `docker-compose pull && docker-compose up -d`
4. Мониторьте использование диска в `downloads/` и `exports/`
5. Настройте ротацию логов

## 📚 Дополнительно

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
