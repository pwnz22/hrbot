import asyncio
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand
from dotenv import load_dotenv

from bot.handlers import setup_handlers
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

    # Устанавливаем команды в меню
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="stats", description="Статистика по откликам"),
        BotCommand(command="recent", description="Последние отклики"),
        BotCommand(command="unprocessed", description="Все необработанные отклики"),
        BotCommand(command="parse", description="Парсить новые письма"),
        BotCommand(command="export", description="Экспорт откликов в Excel")
    ]
    await bot.set_my_commands(commands)

    setup_handlers(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())