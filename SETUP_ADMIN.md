# Настройка первого администратора

После развертывания бота необходимо назначить первого администратора.

## Вариант 1: Через SQL (рекомендуется)

1. Запустите бота и отправьте ему команду `/start` от вашего Telegram аккаунта
2. Подключитесь к базе данных PostgreSQL
3. Найдите ваш `telegram_id`:

```sql
SELECT id, telegram_id, username, first_name, role
FROM telegram_users
ORDER BY created_at DESC;
```

4. Обновите роль на `admin`:

```sql
UPDATE telegram_users
SET role = 'admin'
WHERE telegram_id = YOUR_TELEGRAM_ID;
```

## Вариант 2: Через Python скрипт

Создайте файл `set_admin.py` в корне проекта:

```python
import asyncio
from shared.database.database import AsyncSessionLocal
from shared.models.user import TelegramUser, RoleEnum
from sqlalchemy import select

async def set_admin(telegram_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.role = RoleEnum.ADMIN
            await session.commit()
            print(f"✅ Пользователь {user.first_name} (@{user.username}) назначен администратором")
        else:
            print(f"❌ Пользователь с telegram_id={telegram_id} не найден")
            print("Сначала отправьте боту команду /start")

if __name__ == "__main__":
    # Замените на ваш Telegram ID
    TELEGRAM_ID = 123456789  # Ваш Telegram ID

    asyncio.run(set_admin(TELEGRAM_ID))
```

Запустите скрипт:

```bash
python set_admin.py
```

## Как узнать свой Telegram ID

1. Напишите боту [@userinfobot](https://t.me/userinfobot)
2. Бот вернет ваш Telegram ID

## Роли и права доступа

### 👤 USER (Пользователь)
- Только команда `/start`
- Нет доступа к функционалу

### 👨‍💼 MODERATOR (Модератор)
- Просмотр откликов (`/recent`, `/unprocessed`)
- Изменение статуса откликов
- Экспорт данных (`/export`)
- Парсинг писем (`/parse`)
- Статистика (`/stats`)

### 👑 ADMIN (Администратор)
- Все права модератора
- Управление Gmail аккаунтами (`/accounts`, `/add_account`)
- Управление пользователями (`/users`)

## Управление пользователями

После назначения администратора вы можете управлять ролями других пользователей через команду `/users` в боте.
