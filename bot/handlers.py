from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy import desc
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Application

def setup_handlers(dp: Dispatcher):

    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        await message.answer("Привет! Я HR-бот для обработки откликов на вакансии из Gmail.\n\n"
                           "Команды:\n"
                           "/start - Это сообщение\n"
                           "/stats - Статистика по откликам\n"
                           "/recent - Последние 5 откликов")

    @dp.message(Command("stats"))
    async def stats_handler(message: Message) -> None:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            total = await session.execute(text("SELECT COUNT(*) FROM applications"))
            total_count = total.scalar()

            processed = await session.execute(text("SELECT COUNT(*) FROM applications WHERE is_processed = true"))
            processed_count = processed.scalar()

            unprocessed = total_count - processed_count

            await message.answer(
                f"📊 Статистика:\n"
                f"Всего откликов: {total_count}\n"
                f"Обработано: {processed_count}\n"
                f"Не обработано: {unprocessed}"
            )

    @dp.message(Command("recent"))
    async def recent_handler(message: Message) -> None:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            stmt = select(Application).order_by(desc(Application.created_at)).limit(5)
            result = await session.execute(stmt)
            applications = result.scalars().all()

            if not applications:
                await message.answer("Пока нет откликов")
                return

            text = "📋 Последние 5 откликов:\n\n"
            for app in applications:
                status = "✅" if app.is_processed else "❌"
                text += f"{status} {app.name}\n"
                text += f"📧 {app.email}\n"
                if app.phone:
                    text += f"📱 {app.phone}\n"
                text += f"📅 {app.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

            await message.answer(text)