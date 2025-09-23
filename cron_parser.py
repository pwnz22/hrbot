#!/usr/bin/env python3
"""
Скрипт для автоматического парсинга новых писем по крону
Использует ту же логику что и команда /parse
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.gmail_parser import GmailParser
from shared.database.database import async_engine
from shared.models.vacancy import Base

async def main():
    """Главная функция для парсинга писем"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запуск автоматического парсинга...")

    try:
        # Инициализируем базу данных
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Создаем парсер и парсим новые письма
        parser = GmailParser()
        result = await parser.parse_new_emails()

        if result["parsed_count"] > 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Парсинг завершен!")
            print(f"Обработано новых откликов: {result['parsed_count']}")

            if result["new_vacancies"]:
                print(f"Новые вакансии ({len(result['new_vacancies'])}):")
                for vacancy in result["new_vacancies"]:
                    print(f"  - {vacancy}")
            else:
                print("Новых вакансий не добавлено")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📭 Новых писем не найдено")

    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Ошибка при парсинге: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())