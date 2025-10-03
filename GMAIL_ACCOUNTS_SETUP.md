# Настройка нескольких Gmail аккаунтов

## Обзор

Бот поддерживает работу с несколькими Gmail аккаунтами одновременно. Все аккаунты будут проверяться параллельно при парсинге писем.

## Структура файлов

```
hrbot/
├── gmail_tokens/                    # Папка с токенами и credentials
│   ├── credentials.json            # OAuth приложение (общий для всех аккаунтов)
│   ├── token_main.json             # Token основного аккаунта
│   ├── token_account2.json         # Token второго аккаунта
│   └── token_account3.json         # Token третьего аккаунта
└── bot/
    ├── gmail_accounts.json         # Конфигурация аккаунтов (создать вручную)
    └── gmail_accounts.example.json # Пример конфигурации
```

## Шаги настройки

### 1. Создайте конфигурационный файл

Скопируйте пример конфигурации:

```bash
cp bot/gmail_accounts.example.json bot/gmail_accounts.json
```

### 2. Отредактируйте конфигурацию

Откройте `bot/gmail_accounts.json` и добавьте ваши аккаунты:

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
  },
  {
    "id": "hr_third",
    "name": "Третий HR аккаунт (отключен)",
    "credentials_path": "gmail_tokens/credentials.json",
    "token_path": "gmail_tokens/token_hr_third.json",
    "enabled": false
  }
]
```

**Параметры:**
- `id` - уникальный идентификатор аккаунта (используется в логах)
- `name` - описательное название аккаунта
- `credentials_path` - путь к OAuth приложению (обычно одинаковый для всех)
- `token_path` - путь к token файлу для данного аккаунта
- `enabled` - включить/выключить аккаунт

### 3. Авторизация нового аккаунта

Для каждого нового аккаунта нужно пройти OAuth авторизацию:

```python
from bot.gmail_parser import GmailParser

# Создаем парсер для нового аккаунта
parser = GmailParser(
    account_id="hr_second",
    credentials_path="gmail_tokens/credentials.json",
    token_path="gmail_tokens/token_hr_second.json"
)
```

При первом запуске:
1. Откроется браузер с запросом авторизации
2. Выберите нужный Gmail аккаунт
3. Разрешите доступ к Gmail
4. Token будет сохранен в указанный файл

### 4. Проверка работы

Запустите бота и проверьте парсинг:

```bash
# В боте выполните команду
/parse
```

В логах вы увидите:
```
📧 Проверка аккаунта: main
📧 Проверка аккаунта: hr_second
✅ [main] Обработано откликов: 5
✅ [hr_second] Обработано откликов: 3
📊 Всего обработано откликов: 8
```

## Управление аккаунтами

### Временное отключение аккаунта

Установите `"enabled": false` в конфигурации:

```json
{
  "id": "hr_third",
  "enabled": false
}
```

### Добавление нового аккаунта

1. Добавьте запись в `bot/gmail_accounts.json`
2. Укажите новый `token_path` (например, `token_new_account.json`)
3. Перезапустите бота - при первом парсинге будет запрошена авторизация

### Удаление аккаунта

1. Удалите запись из `bot/gmail_accounts.json`
2. Удалите соответствующий token файл
3. Перезапустите бота

## Безопасность

⚠️ **Важно:**
- Файлы `token_*.json` и `bot/gmail_accounts.json` содержат приватные данные
- Они автоматически добавлены в `.gitignore`
- НЕ коммитьте эти файлы в Git
- Используйте `gmail_accounts.example.json` как пример для других разработчиков

## Автоматическая проверка (Scheduler)

Scheduler автоматически загружает все активные аккаунты из конфигурации и проверяет их параллельно каждые N минут (по умолчанию 5).

Проверить работу scheduler:

```bash
# В логах вы увидите:
📧 Добавлен аккаунт: Основной HR аккаунт
📧 Добавлен аккаунт: Второй HR аккаунт
🚀 Scheduler запущен. Интервал проверки: 5 мин.
```

## Troubleshooting

### Ошибка авторизации

Если token устарел, удалите файл и пройдите авторизацию заново:

```bash
rm gmail_tokens/token_hr_second.json
# Перезапустите бота - будет запрошена повторная авторизация
```

### Аккаунт не проверяется

Проверьте:
1. `"enabled": true` в конфигурации
2. Существует ли token файл
3. Корректны ли пути в конфигурации

### Все аккаунты отключены

Если в конфигурации нет активных аккаунтов, будет использован дефолтный:
- gmail_tokens/credentials.json
- gmail_tokens/token_main.json

## Пример использования

```python
# bot/main.py
from bot.scheduler import GmailScheduler

# Scheduler автоматически загрузит все аккаунты из gmail_accounts.json
scheduler = GmailScheduler(interval_minutes=5)
await scheduler.start_background()
```

Готово! Теперь бот будет собирать вакансии со всех подключенных Gmail аккаунтов.
