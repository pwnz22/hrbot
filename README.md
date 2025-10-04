# HR Bot

Telegram бот для автоматизации обработки откликов на вакансии из Gmail с поддержкой ролей, множественных аккаунтов и AI-анализа резюме.

## 📋 Содержание

- [Возможности](#возможности)
- [Быстрый старт](#быстрый-старт)
- [Архитектура](#архитектура)
- [Настройка](#настройка)
- [Управление пользователями](#управление-пользователями)
- [Gmail интеграция](#gmail-интеграция)
- [Docker развертывание](#docker-развертывание)
- [Команды бота](#команды-бота)

## 🎯 Возможности

- 🤖 **Telegram бот** - полноценный интерфейс для работы с откликами
- 👥 **Система ролей** - USER, MODERATOR, ADMIN с гибким управлением правами
- 📧 **Поддержка множественных Gmail аккаунтов** - парсинг из нескольких почтовых ящиков
- 🔄 **Автоматический парсинг** - проверка новых писем по расписанию
- 🧠 **AI-анализ резюме** - автоматическое резюмирование с помощью Google Gemini
- 📊 **Экспорт в Excel** - выгрузка всех откликов с анализом

## 🚀 Быстрый старт

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- Telegram бот токен
- Google Gemini API ключ (опционально)
- Gmail OAuth credentials (опционально)

### Установка

```bash
# 1. Клонируйте репозиторий
git clone <repository-url>
cd hrbot

# 2. Создайте .env файл
cp .env.example .env
nano .env

# 3. Запустите проект
./docker-deploy-bot.sh
```

### Минимальная конфигурация .env

```env
BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///./hrbot.db
GEMINI_API_KEY=your_gemini_api_key
GMAIL_CHECK_INTERVAL=5
```

## 🏗 Архитектура

### Структура проекта

```
hrbot/
├── bot/                           # Telegram бот (Aiogram)
│   ├── main.py                   # Точка входа
│   ├── handlers.py               # Обработчики команд
│   ├── middleware.py             # Проверка ролей и прав
│   ├── gmail_parser.py           # Парсер Gmail
│   ├── gmail_account_manager.py  # Управление аккаунтами
│   └── gmail_accounts.json       # Конфигурация аккаунтов
├── shared/                       # Общие модули
│   ├── database/
│   ├── models/
│   │   ├── vacancy.py           # Модели вакансий
│   │   └── user.py              # Модели пользователей
│   └── services/
│       ├── gemini_service.py    # AI анализ
│       └── resume_summary_service.py
├── gmail_tokens/                 # OAuth токены
│   ├── credentials.json
│   └── token_*.json
├── downloads/                    # Скачанные резюме
├── exports/                      # Excel экспорты
└── docker-compose.yml
```

### Docker сервис

**bot** - Telegram бот с автоматическим парсингом Gmail

## ⚙️ Настройка

### 1. Настройка первого администратора

После первого запуска необходимо назначить администратора:

```bash
# Отправьте боту /start от вашего Telegram аккаунта

# Подключитесь к базе данных
docker exec -it hrbot-telegram sqlite3 hrbot.db

# Найдите свой telegram_id
SELECT id, telegram_id, username, first_name, role FROM telegram_users;

# Назначьте роль админа (замените YOUR_TELEGRAM_ID)
UPDATE telegram_users SET role = 'admin' WHERE telegram_id = YOUR_TELEGRAM_ID;

# Проверьте
SELECT telegram_id, username, role FROM telegram_users;

# Выйдите
.quit
```

**Как узнать свой Telegram ID:**
Напишите боту [@userinfobot](https://t.me/userinfobot)

### 2. Роли и права доступа

#### 👤 USER (Пользователь)
- Только команда `/start`
- Нет доступа к функционалу

#### 👨‍💼 MODERATOR (Модератор)
- Просмотр откликов (`/recent`, `/unprocessed`)
- Изменение статуса откликов
- Экспорт данных (`/export`)
- Парсинг писем (`/parse`)
- Статистика (`/stats`)

#### 👑 ADMIN (Администратор)
- Все права модератора
- Управление Gmail аккаунтами (`/accounts`, `/add_account`)
- Управление пользователями (`/users`)

## 📧 Gmail интеграция

### Настройка OAuth приложения

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com)
2. Создайте новый проект или выберите существующий
3. Включите Gmail API
4. Создайте OAuth 2.0 credentials
5. Скачайте `credentials.json` и поместите в `gmail_tokens/`

### Добавление Gmail аккаунта через бота

```bash
# В боте выполните команду (только для админов)
/add_account

# Бот отправит OAuth ссылку
# Перейдите по ссылке, авторизуйтесь
# Скопируйте код и отправьте боту
# Token будет создан автоматически
```

### Управление несколькими аккаунтами

Конфигурация аккаунтов в `bot/gmail_accounts.json`:

```json
[
  {
    "id": "main",
    "name": "Основной HR аккаунт",
    "credentials_path": "gmail_tokens/credentials.json",
    "token_path": "gmail_tokens/token_main.json",
    "enabled": true
  },
  {
    "id": "hr_second",
    "name": "Второй HR аккаунт",
    "credentials_path": "gmail_tokens/credentials.json",
    "token_path": "gmail_tokens/token_hr_second.json",
    "enabled": true
  }
]
```

Управление через бота:
- `/accounts` - список всех аккаунтов
- `/add_account` - добавить новый аккаунт
- В `/accounts` можно включать/отключать аккаунты

## 🐳 Docker развертывание

### Запуск бота

```bash
./docker-deploy-bot.sh
```

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только бот
docker-compose logs -f bot

# Последние 50 строк
docker-compose logs --tail=50 bot
```

### Перезапуск

```bash
docker-compose restart bot
```

### Обновление на сервере

```bash
cd /path/to/hrbot
git pull
./docker-deploy-bot.sh
```

### Полная пересборка

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🤖 Команды бота

### Для всех пользователей
- `/start` - Главное меню

### Для модераторов и админов
- `/stats` - Статистика по откликам
- `/recent` - Список вакансий с откликами
- `/unprocessed` - Все необработанные отклики
- `/parse` - Парсить новые письма из Gmail
- `/export` - Экспорт откликов в Excel

### Только для админов
- `/users` - Управление пользователями и ролями
- `/accounts` - Управление Gmail аккаунтами
- `/add_account` - Добавить новый Gmail аккаунт
- `/cancel` - Отменить текущую операцию

## 🧠 AI-анализ резюме

### Настройка

1. Получите API ключ: https://makersuite.google.com/app/apikey
2. Добавьте в `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key
```

### Использование

1. Откройте отклик с прикрепленным резюме (.pdf/.docx)
2. Нажмите **"🤖 Сгенерировать анализ резюме"**
3. Бот проанализирует резюме и сохранит результат
4. Повторные нажатия показывают готовый анализ

### Формат анализа

```
📋 Вакансия: [название]
👤 Кандидат: [имя]
📧 Email: [email]
📱 Телефон: [телефон]
🔗 GitHub: [ссылка]
📝 Краткое резюме: [3-4 предложения]
🛠 Ключевые навыки: [список]
⏰ Опыт работы: [X лет]
🎓 Образование: [описание]
⚠️ Потенциальные риски: [если есть]
```

Анализ также включается в Excel экспорт.

## 🔧 Управление

### Создание директорий

```bash
mkdir -p downloads exports logs gmail_tokens bot
```

### Права на файлы

```bash
chmod 666 hrbot.db
chmod 666 bot/gmail_accounts.json
```

### Backup базы данных

```bash
# Создать backup
cp hrbot.db hrbot.db.backup

# Восстановить из backup
cp hrbot.db.backup hrbot.db
```

## 🐛 Troubleshooting

### Бот не запускается

```bash
docker-compose logs bot
docker-compose exec bot env | grep BOT_TOKEN
docker-compose restart bot
```

### Gmail авторизация не работает

```bash
# Проверьте credentials.json
docker-compose exec bot ls -la /app/gmail_tokens/credentials.json

# Удалите token и пройдите авторизацию заново
rm gmail_tokens/token_main.json
docker-compose restart bot
```

### Ошибка "No module named 'openpyxl'"

```bash
# Пересоберите образ с новыми зависимостями
docker-compose build --no-cache bot
docker-compose up -d bot
```

### База данных недоступна

```bash
# Проверьте права
ls -la hrbot.db

# Проверьте в контейнере
docker-compose exec bot ls -la /app/hrbot.db
```

## 📝 Разработка

### Локальный запуск (без Docker)

```bash
# Установите зависимости
pip install -r requirements.txt

# Запустите бота
python -m bot.main
```

### Тестирование

```bash
# Проверка синтаксиса
python -m py_compile bot/handlers.py

# Запуск тестов
pytest
```

## 🔒 Безопасность

⚠️ **Важно:**

1. **Никогда** не коммитьте `.env` в git
2. **Никогда** не коммитьте `credentials.json` и `token_*.json`
3. **Никогда** не коммитьте `bot/gmail_accounts.json`
4. Храните API ключи в секретах
5. На production используйте SSL/TLS
6. Ограничьте доступ к портам через firewall

Все чувствительные файлы уже добавлены в `.gitignore`.

## 📚 Технологии

- **Python 3.11+**
- **Aiogram 3.10** - Telegram Bot Framework
- **SQLAlchemy** - ORM
- **SQLite** - База данных
- **Google Gmail API** - Интеграция с почтой
- **Google Gemini** - AI анализ резюме
- **OpenPyXL** - Excel экспорт
- **Docker & Docker Compose** - Контейнеризация

## 📄 Лицензия

MIT License

## 🤝 Поддержка

Если возникли вопросы или проблемы:
1. Проверьте логи: `docker-compose logs -f bot`
2. Изучите документацию выше
3. Создайте issue в репозитории
