# Миграция базы данных

## Обновление до версии с поддержкой привязки Gmail аккаунтов

После обновления кода необходимо выполнить миграцию базы данных.

### Локальная разработка

```bash
python migrate_db.py
```

### На сервере через Docker

```bash
# Остановить контейнер
docker-compose stop bot

# Выполнить миграцию
docker-compose exec bot python migrate_db.py

# Или если контейнер остановлен
docker-compose run --rm bot python migrate_db.py

# Запустить контейнер
docker-compose start bot
```

### Что делает миграция

1. Создает таблицу `gmail_accounts` для хранения информации об аккаунтах
2. Добавляет колонку `gmail_account_id` в таблицу `vacancies` для связи вакансий с аккаунтами

### Проверка миграции

```bash
# Локально
sqlite3 hrbot.db "PRAGMA table_info(vacancies)"
sqlite3 hrbot.db "PRAGMA table_info(gmail_accounts)"

# В Docker
docker-compose exec bot sqlite3 hrbot.db "PRAGMA table_info(vacancies)"
```

### Откат (при необходимости)

⚠️ **Внимание**: Откат удалит данные о привязках аккаунтов!

```bash
sqlite3 hrbot.db "ALTER TABLE vacancies DROP COLUMN gmail_account_id"
sqlite3 hrbot.db "DROP TABLE gmail_accounts"
```
