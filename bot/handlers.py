from aiogram import Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from sqlalchemy import desc, select
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Application, Vacancy

# Словарь для хранения ID сообщений с файлами резюме для каждого пользователя
user_resume_messages = {}

class VacancyCallback(CallbackData, prefix="vacancy"):
    vacancy_id: int

class ApplicationCallback(CallbackData, prefix="application"):
    application_id: int

class ProcessCallback(CallbackData, prefix="process"):
    application_id: int
    action: str  # "mark_processed" или "mark_unprocessed"

class BackCallback(CallbackData, prefix="back"):
    to: str  # "vacancies" или "applications"
    vacancy_id: int = 0  # Для возврата к приложениям конкретной вакансии

async def delete_message_after_delay(message, delay_seconds):
    """Удаляет сообщение через указанное количество секунд"""
    import asyncio
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception:
        pass  # Игнорируем ошибки если сообщение уже удалено

def setup_handlers(dp: Dispatcher):

    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        await message.answer("Привет! Я HR-бот для обработки откликов на вакансии из Gmail.\n\n"
                           "Команды:\n"
                           "/start - Это сообщение\n"
                           "/stats - Статистика по откликам\n"
                           "/recent - Последние отклики\n"
                           "/parse - Парсить новые письма")

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
                f"Всего откликов: <b>{total_count}</b>\n"
                f"Обработано: <b>{processed_count}</b>\n"
                f"Не обработано: <b>{unprocessed}</b>",
                parse_mode="HTML"
            )

    @dp.message(Command("recent"))
    async def recent_handler(message: Message) -> None:
        async with AsyncSessionLocal() as session:
            # Получаем список вакансий с количеством откликов
            stmt = select(Vacancy).order_by(desc(Vacancy.created_at))
            result = await session.execute(stmt)
            vacancies = result.scalars().all()

            if not vacancies:
                await message.answer("Пока нет вакансий")
                return

            # Создаем клавиатуру с вакансиями
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])

            for vacancy in vacancies:
                # Считаем количество откликов для каждой вакансии
                count_stmt = select(Application).where(Application.vacancy_id == vacancy.id)
                count_result = await session.execute(count_stmt)
                applications_count = len(count_result.scalars().all())

                button_text = f"{vacancy.title} ({applications_count} откликов)"
                button = InlineKeyboardButton(
                    text=button_text,
                    callback_data=VacancyCallback(vacancy_id=vacancy.id).pack()
                )
                keyboard.inline_keyboard.append([button])

            await message.answer("📋 Выберите вакансию для просмотра откликов:", reply_markup=keyboard)

    @dp.message(Command("parse"))
    async def parse_handler(message: Message) -> None:
        await message.answer("🔄 Начинаю парсинг новых писем...")

        try:
            from bot.gmail_parser import GmailParser
            parser = GmailParser()

            # Парсим новые письма
            result = await parser.parse_new_emails()

            if result["parsed_count"] > 0:
                text = f"✅ Парсинг завершен!\nОбработано новых откликов: <b>{result['parsed_count']}</b>"

                if result["new_vacancies"]:
                    text += f"\n\n<b>Новые вакансии ({len(result['new_vacancies'])}):</b>"
                    for vacancy in result["new_vacancies"]:
                        text += f"\n• {vacancy}"

                await message.answer(text, parse_mode="HTML")
            else:
                await message.answer("📭 Новых писем не найдено")

        except Exception as e:
            await message.answer(f"❌ Ошибка при парсинге: {str(e)}")

    @dp.callback_query(VacancyCallback.filter())
    async def vacancy_applications_handler(query: CallbackQuery, callback_data: VacancyCallback) -> None:
        await query.answer()

        async with AsyncSessionLocal() as session:
            # Получаем вакансию
            vacancy_stmt = select(Vacancy).where(Vacancy.id == callback_data.vacancy_id)
            vacancy_result = await session.execute(vacancy_stmt)
            vacancy = vacancy_result.scalar_one_or_none()

            if not vacancy:
                await query.message.edit_text("Вакансия не найдена")
                return

            # Получаем отклики на эту вакансию
            apps_stmt = select(Application).where(Application.vacancy_id == callback_data.vacancy_id).order_by(desc(Application.created_at))
            apps_result = await session.execute(apps_stmt)
            applications = apps_result.scalars().all()

            if not applications:
                await query.message.edit_text(f"📋 Вакансия: {vacancy.title}\n\nОткликов пока нет")
                return

            # Создаем клавиатуру с откликами
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])

            for app in applications:
                # Формируем текст кнопки: {имя} - {телефон} - {email}
                button_text = app.name
                if app.phone:
                    button_text += f" - {app.phone}"
                if app.email:
                    button_text += f" - {app.email}"

                # Добавляем статус обработки
                status = "✅" if app.is_processed else "❌"
                button_text = f"{status} {button_text}"

                button = InlineKeyboardButton(
                    text=button_text,
                    callback_data=ApplicationCallback(application_id=app.id).pack()
                )
                keyboard.inline_keyboard.append([button])

            # Добавляем кнопку "Назад к вакансиям"
            back_button = InlineKeyboardButton(
                text="⬅️ Назад к вакансиям",
                callback_data=BackCallback(to="vacancies").pack()
            )
            keyboard.inline_keyboard.append([back_button])

            text = f"📋 Вакансия: <b>{vacancy.title}</b>\n"
            text += f"📊 Всего откликов: <b>{len(applications)}</b>\n\n"
            text += "Выберите отклик для просмотра подробностей:"

            await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.callback_query(ApplicationCallback.filter())
    async def application_details_handler(query: CallbackQuery, callback_data: ApplicationCallback) -> None:
        await query.answer()

        async with AsyncSessionLocal() as session:
            # Получаем отклик
            app_stmt = select(Application).where(Application.id == callback_data.application_id)
            app_result = await session.execute(app_stmt)
            application = app_result.scalar_one_or_none()

            if not application:
                await query.message.edit_text("Отклик не найден")
                return

            # Получаем вакансию
            vacancy_stmt = select(Vacancy).where(Vacancy.id == application.vacancy_id)
            vacancy_result = await session.execute(vacancy_stmt)
            vacancy = vacancy_result.scalar_one_or_none()

            # Формируем детальную информацию
            status = "✅ Обработан" if application.is_processed else "❌ Не обработан"

            text = f"👤 <b>{application.name}</b>\n\n"
            text += f"📋 Вакансия: {vacancy.title if vacancy else 'Неизвестно'}\n"
            text += f"📧 Email: {application.email or 'Не указан'}\n"
            text += f"📱 Телефон: {application.phone or 'Не указан'}\n"
            text += f"🏷️ Статус: {status}\n"
            text += f"📅 Дата отклика: {application.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

            if application.applicant_message:
                text += f"💬 <b>Сообщение от кандидата:</b>\n{application.applicant_message}\n\n"

            if application.attachment_filename:
                text += f"📎 <b>Вложение:</b> {application.attachment_filename}\n"
                if application.file_url:
                    text += f"🔗 <a href='{application.file_url}'>Ссылка на файл</a>\n\n"

            # Создаем кнопки для изменения статуса обработки и навигации
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            if application.is_processed:
                process_button = InlineKeyboardButton(
                    text="❌ Отменить обработку",
                    callback_data=ProcessCallback(application_id=application.id, action="mark_unprocessed").pack()
                )
            else:
                process_button = InlineKeyboardButton(
                    text="✅ Отметить как обработанный",
                    callback_data=ProcessCallback(application_id=application.id, action="mark_processed").pack()
                )
            keyboard.inline_keyboard.append([process_button])

            # Добавляем кнопку "Назад к откликам"
            back_button = InlineKeyboardButton(
                text="⬅️ Назад к откликам",
                callback_data=BackCallback(to="applications", vacancy_id=application.vacancy_id).pack()
            )
            keyboard.inline_keyboard.append([back_button])

            # Отправляем сообщение с информацией
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

            # Если есть файл, отправляем его и сохраняем ID сообщения
            user_id = query.from_user.id
            if application.file_path and os.path.exists(application.file_path):
                try:
                    from aiogram.types import FSInputFile
                    file = FSInputFile(application.file_path, filename=application.attachment_filename)
                    file_msg = await query.message.answer_document(file, caption=f"📎 Резюме от {application.name}")
                    # Сохраняем ID сообщения с файлом
                    user_resume_messages[user_id] = file_msg.message_id
                except Exception as e:
                    error_msg = await query.message.answer(f"❌ Ошибка при отправке файла: {str(e)}")
                    user_resume_messages[user_id] = error_msg.message_id
            elif application.file_url:
                url_msg = await query.message.answer(f"📎 Файл доступен по ссылке: {application.file_url}")
                user_resume_messages[user_id] = url_msg.message_id

    @dp.callback_query(ProcessCallback.filter())
    async def process_status_handler(query: CallbackQuery, callback_data: ProcessCallback) -> None:
        await query.answer()

        async with AsyncSessionLocal() as session:
            # Получаем отклик
            app_stmt = select(Application).where(Application.id == callback_data.application_id)
            app_result = await session.execute(app_stmt)
            application = app_result.scalar_one_or_none()

            if not application:
                await query.message.edit_text("❌ Отклик не найден")
                return

            # Изменяем статус обработки
            if callback_data.action == "mark_processed":
                application.is_processed = True
                status_message = "✅ Отклик отмечен как обработанный"
            elif callback_data.action == "mark_unprocessed":
                application.is_processed = False
                status_message = "❌ Обработка отклика отменена"

            # Сохраняем изменения
            await session.commit()

            # Получаем вакансию для обновления информации
            vacancy_stmt = select(Vacancy).where(Vacancy.id == application.vacancy_id)
            vacancy_result = await session.execute(vacancy_stmt)
            vacancy = vacancy_result.scalar_one_or_none()

            # Обновляем сообщение с новой информацией
            status = "✅ Обработан" if application.is_processed else "❌ Не обработан"

            text = f"👤 <b>{application.name}</b>\n\n"
            text += f"📋 Вакансия: {vacancy.title if vacancy else 'Неизвестно'}\n"
            text += f"📧 Email: {application.email or 'Не указан'}\n"
            text += f"📱 Телефон: {application.phone or 'Не указан'}\n"
            text += f"🏷️ Статус: {status}\n"
            text += f"📅 Дата отклика: {application.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

            if application.applicant_message:
                text += f"💬 <b>Сообщение от кандидата:</b>\n{application.applicant_message}\n\n"

            if application.attachment_filename:
                text += f"📎 <b>Вложение:</b> {application.attachment_filename}\n"
                if application.file_url:
                    text += f"🔗 <a href='{application.file_url}'>Ссылка на файл</a>\n\n"

            # Создаем обновленные кнопки
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            if application.is_processed:
                process_button = InlineKeyboardButton(
                    text="❌ Отменить обработку",
                    callback_data=ProcessCallback(application_id=application.id, action="mark_unprocessed").pack()
                )
            else:
                process_button = InlineKeyboardButton(
                    text="✅ Отметить как обработанный",
                    callback_data=ProcessCallback(application_id=application.id, action="mark_processed").pack()
                )
            keyboard.inline_keyboard.append([process_button])

            # Добавляем кнопку "Назад к откликам"
            back_button = InlineKeyboardButton(
                text="⬅️ Назад к откликам",
                callback_data=BackCallback(to="applications", vacancy_id=application.vacancy_id).pack()
            )
            keyboard.inline_keyboard.append([back_button])

            # Обновляем сообщение
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

            # Отправляем уведомление об изменении статуса и удаляем через секунду
            status_msg = await query.message.answer(status_message)

            # Удаляем сообщение через 1 секунду
            import asyncio
            asyncio.create_task(delete_message_after_delay(status_msg, 1))

    @dp.callback_query(BackCallback.filter())
    async def back_handler(query: CallbackQuery, callback_data: BackCallback) -> None:
        await query.answer()

        # Удаляем сообщение с файлом резюме если оно есть
        user_id = query.from_user.id
        if user_id in user_resume_messages:
            try:
                await query.bot.delete_message(chat_id=query.message.chat.id, message_id=user_resume_messages[user_id])
            except Exception:
                pass  # Игнорируем ошибки если сообщение уже удалено
            del user_resume_messages[user_id]

        if callback_data.to == "vacancies":
            # Возвращаемся к списку вакансий
            async with AsyncSessionLocal() as session:
                stmt = select(Vacancy).order_by(desc(Vacancy.created_at))
                result = await session.execute(stmt)
                vacancies = result.scalars().all()

                if not vacancies:
                    await query.message.edit_text("Пока нет вакансий")
                    return

                keyboard = InlineKeyboardMarkup(inline_keyboard=[])

                for vacancy in vacancies:
                    count_stmt = select(Application).where(Application.vacancy_id == vacancy.id)
                    count_result = await session.execute(count_stmt)
                    applications_count = len(count_result.scalars().all())

                    button_text = f"{vacancy.title} ({applications_count} откликов)"
                    button = InlineKeyboardButton(
                        text=button_text,
                        callback_data=VacancyCallback(vacancy_id=vacancy.id).pack()
                    )
                    keyboard.inline_keyboard.append([button])

                await query.message.edit_text("📋 Выберите вакансию для просмотра откликов:", reply_markup=keyboard)

        elif callback_data.to == "applications":
            # Возвращаемся к списку откликов конкретной вакансии
            async with AsyncSessionLocal() as session:
                vacancy_stmt = select(Vacancy).where(Vacancy.id == callback_data.vacancy_id)
                vacancy_result = await session.execute(vacancy_stmt)
                vacancy = vacancy_result.scalar_one_or_none()

                if not vacancy:
                    await query.message.edit_text("Вакансия не найдена")
                    return

                apps_stmt = select(Application).where(Application.vacancy_id == callback_data.vacancy_id).order_by(desc(Application.created_at))
                apps_result = await session.execute(apps_stmt)
                applications = apps_result.scalars().all()

                if not applications:
                    await query.message.edit_text(f"📋 Вакансия: {vacancy.title}\n\nОткликов пока нет")
                    return

                keyboard = InlineKeyboardMarkup(inline_keyboard=[])

                for app in applications:
                    button_text = app.name
                    if app.phone:
                        button_text += f" - {app.phone}"
                    if app.email:
                        button_text += f" - {app.email}"

                    status = "✅" if app.is_processed else "❌"
                    button_text = f"{status} {button_text}"

                    button = InlineKeyboardButton(
                        text=button_text,
                        callback_data=ApplicationCallback(application_id=app.id).pack()
                    )
                    keyboard.inline_keyboard.append([button])

                # Добавляем кнопку "Назад к вакансиям"
                back_button = InlineKeyboardButton(
                    text="⬅️ Назад к вакансиям",
                    callback_data=BackCallback(to="vacancies").pack()
                )
                keyboard.inline_keyboard.append([back_button])

                text = f"📋 Вакансия: <b>{vacancy.title}</b>\n"
                text += f"📊 Всего откликов: <b>{len(applications)}</b>\n\n"
                text += "Выберите отклик для просмотра подробностей:"

                await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")