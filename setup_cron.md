# Настройка автоматического парсинга через cron

## Скрипт для крона

Создан скрипт `cron_parser.py` который:
- Автоматически парсит новые письма
- Использует ту же логику что и команда `/parse`
- Выводит информацию о новых откликах и вакансиях
- Логирует все операции с временными метками

## Установка cron задачи

### 1. Открыть crontab для редактирования:
```bash
crontab -e
```

### 2. Добавить одну из следующих строк:

**Каждые 5 минут:**
```
*/5 * * * * cd /Users/valijon/Documents/Sites/hrbot && /Users/valijon/.pyenv/versions/3.11.10/bin/python cron_parser.py >> logs/cron_parser.log 2>&1
```

**Каждые 10 минут:**
```
*/10 * * * * cd /Users/valijon/Documents/Sites/hrbot && /Users/valijon/.pyenv/versions/3.11.10/bin/python cron_parser.py >> logs/cron_parser.log 2>&1
```

**Каждые 30 минут:**
```
*/30 * * * * cd /Users/valijon/Documents/Sites/hrbot && /Users/valijon/.pyenv/versions/3.11.10/bin/python cron_parser.py >> logs/cron_parser.log 2>&1
```

**Каждый час:**
```
0 * * * * cd /Users/valijon/Documents/Sites/hrbot && /Users/valijon/.pyenv/versions/3.11.10/bin/python cron_parser.py >> logs/cron_parser.log 2>&1
```

## Создание директории для логов

```bash
mkdir -p /Users/valijon/Documents/Sites/hrbot/logs
```

## Проверка работы

### Просмотр логов:
```bash
tail -f /Users/valijon/Documents/Sites/hrbot/logs/cron_parser.log
```

### Просмотр активных cron задач:
```bash
crontab -l
```

### Ручной запуск для тестирования:
```bash
cd /Users/valijon/Documents/Sites/hrbot
python cron_parser.py
```

## Формат вывода

Скрипт выводит:
- Временную метку начала парсинга
- Количество обработанных откликов
- Список новых вакансий (если есть)
- Сообщения об ошибках (если есть)

## Пример лога:
```
[2024-01-15 10:00:01] Запуск автоматического парсинга...
[2024-01-15 10:00:03] ✅ Парсинг завершен!
Обработано новых откликов: 2
Новые вакансии (1):
  - Frontend разработчик
```

## Остановка cron

Для остановки автоматического парсинга:
```bash
crontab -e
# Закомментировать или удалить строку с cron_parser.py
```