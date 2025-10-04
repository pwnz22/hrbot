# Инструкция по пересозданию базы данных

## На продакшен сервере

### 1. Остановить контейнеры
```bash
cd /var/opt/Docker/hrbot
docker-compose down
```

### 2. Удалить старую базу данных
```bash
rm -f hrbot.db
```

### 3. Удалить кэш Alembic (если есть)
```bash
rm -rf alembic/versions/__pycache__
```

### 4. Создать новую БД через Alembic
```bash
docker-compose run --rm bot alembic upgrade head
```

### 5. Запустить контейнеры
```bash
docker-compose up -d
```

### 6. Проверить структуру БД
```bash
docker-compose exec bot python -c "
import sqlite3
conn = sqlite3.connect('hrbot.db')
cursor = conn.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
tables = [row[0] for row in cursor]
print('Таблицы в БД:', tables)
conn.close()
"
```

Должны быть таблицы:
- telegram_users
- gmail_accounts
- vacancies
- applications

## В локальной разработке

```bash
./reset_db.sh
```

## Примечание
После пересоздания БД:
- Все пользователи будут удалены - нужно заново авторизоваться в боте
- Все вакансии будут удалены - нужно запустить парсинг заново
- Gmail аккаунты нужно будет добавить заново через бота
