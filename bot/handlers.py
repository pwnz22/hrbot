from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy import desc
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Vacancy

def setup_handlers(dp: Dispatcher):

    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        await message.answer("Привет! Я HR-бот для обработки вакансий из Gmail.\n\n"
                           "Команды:\n"
                           "/start - Это сообщение\n"
                           "/stats - Статистика по вакансиям\n"
                           "/recent - Последние 5 вакансий")

    @dp.message(Command("stats"))
    async def stats_handler(message: Message) -> None:
        async with AsyncSessionLocal() as session:
            total = await session.execute("SELECT COUNT(*) FROM vacancies")
            total_count = total.scalar()

            processed = await session.execute("SELECT COUNT(*) FROM vacancies WHERE is_processed = true")
            processed_count = processed.scalar()

            unprocessed = total_count - processed_count

            await message.answer(
                f"📊 Статистика:\n"
                f"Всего вакансий: {total_count}\n"
                f"Обработано: {processed_count}\n"
                f"Не обработано: {unprocessed}"
            )

    @dp.message(Command("recent"))
    async def recent_handler(message: Message) -> None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                session.query(Vacancy)
                .order_by(desc(Vacancy.created_at))
                .limit(5)
            )
            vacancies = result.scalars().all()

            if not vacancies:
                await message.answer("Пока нет вакансий")
                return

            text = "📋 Последние 5 вакансий:\n\n"
            for vacancy in vacancies:
                status = "✅" if vacancy.is_processed else "❌"
                text += f"{status} {vacancy.name}\n"
                text += f"📧 {vacancy.email}\n"
                if vacancy.phone:
                    text += f"📱 {vacancy.phone}\n"
                text += f"📅 {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

            await message.answer(text)