# HR Bot

Telegram бот для парсинга вакансий из Gmail и API для получения данных.

## 🚀 Быстрый старт с Docker

Развернуть весь проект одной командой:

```bash
./docker-deploy.sh
```

Подробнее: [DOCKER.md](DOCKER.md)

## Структура проекта

```
hrbot/
├── api/                    # FastAPI приложение
│   ├── main.py            # Основной файл API
│   └── schemas.py         # Pydantic модели
├── bot/                   # Aiogram бот
│   ├── main.py           # Основной файл бота
│   ├── handlers.py       # Обработчики команд
│   └── gmail_parser.py   # Парсер Gmail
├── shared/               # Общие модули
│   ├── database/         # Настройки БД
│   ├── models/          # SQLAlchemy модели
│   └── config/          # Конфигурация
├── downloads/           # Папка для загруженных файлов
├── requirements.txt     # Зависимости
├── run_api.py          # Запуск API
└── run_bot.py          # Запуск бота
```

## Установка

1. Установить зависимости:
```bash
pip install -r requirements.txt
```

2. Создать файл `.env`:
```bash
cp .env.example .env
```

3. Заполнить `.env` файл с токеном бота

4. Настроить Gmail API:
   - Создать проект в Google Cloud Console
   - Включить Gmail API
   - Скачать `credentials.json`

## Запуск

### Вариант 1: Docker (рекомендуется)

```bash
# Настройте .env
cp .env.example .env
nano .env

# Запустите все сервисы
./docker-deploy.sh

# Просмотр логов
./docker-logs.sh
```

Подробнее: [DOCKER.md](DOCKER.md)

### Вариант 2: Локальный запуск

#### API сервер:
```bash
python run_api.py
# или
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

#### Telegram бот:
```bash
python run_bot.py
# или
python -m bot.main
```

## API Endpoints

- `GET /vacancies` - Получить список вакансий
- `GET /vacancies/{id}` - Получить конкретную вакансию
- `PUT /vacancies/{id}/processed` - Отметить как обработанную
- `GET /stats` - Статистика

## Команды бота

- `/start` - Приветствие
- `/stats` - Статистика по вакансиям
- `/recent` - Последние 5 вакансий