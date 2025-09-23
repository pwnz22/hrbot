import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv

from bot.handlers import setup_handlers
from bot.gmail_parser import GmailParser
from shared.database.database import async_engine
from shared.models.vacancy import Base

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

async def main():
    if not TOKEN:
        logging.error("BOT_TOKEN не найден в переменных окружения")
        return

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(TOKEN)
    dp = Dispatcher()

    setup_handlers(dp)

    gmail_parser = GmailParser()

    async def check_gmail():
        while True:
            try:
                await gmail_parser.parse_new_emails()
                await asyncio.sleep(300)  # Проверяем каждые 5 минут
            except Exception as e:
                logging.error(f"Ошибка при парсинге Gmail: {e}")
                await asyncio.sleep(60)

    task = asyncio.create_task(check_gmail())

    try:
        await dp.start_polling(bot)
    finally:
        task.cancel()
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())