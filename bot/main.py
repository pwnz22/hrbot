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
from bot.scheduler import GmailScheduler
from shared.database.database import async_engine
from shared.models.vacancy import Base
from shared.models.user import TelegramUser

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GMAIL_CHECK_INTERVAL = int(os.getenv("GMAIL_CHECK_INTERVAL", "5"))  # По умолчанию 5 минут

async def main():
    if not TOKEN:
        logging.error("BOT_TOKEN не найден в переменных окружения")
        return

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    bot = Bot(TOKEN)
    dp = Dispatcher()

    # Регистрируем middleware для проверки ролей
    from bot.middleware import RoleCheckMiddleware
    dp.message.middleware(RoleCheckMiddleware())
    dp.callback_query.middleware(RoleCheckMiddleware())

    # Команды будут устанавливаться динамически в зависимости от роли пользователя
    # в обработчике /start

    setup_handlers(dp)

    # Запускаем scheduler в фоновом режиме (только если есть credentials)
    scheduler = None
    try:
        import os
        if os.path.exists('gmail_tokens/credentials.json'):
            scheduler = GmailScheduler(interval_minutes=GMAIL_CHECK_INTERVAL)
            await scheduler.start_background()
            print("✅ Gmail scheduler запущен")
        else:
            print("⚠️ Gmail credentials не найден, scheduler отключен")
    except Exception as e:
        print(f"⚠️ Не удалось запустить Gmail scheduler: {e}")

    try:
        await dp.start_polling(bot)
    finally:
        if scheduler:
            await scheduler.stop()
        await bot.session.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())