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
from shared.services.resume_summary_service import ResumeSummaryService

# Словарь для хранения ID сообщений с файлами резюме для каждого пользователя
user_resume_messages = {}

class VacancyCallback(CallbackData, prefix="vacancy"):
    vacancy_id: int

class ApplicationCallback(CallbackData, prefix="application"):
    application_id: int
    source: str = "recent"  # "recent", "unprocessed" или "vacancy"

class ProcessCallback(CallbackData, prefix="process"):
    application_id: int
    action: str  # "mark_processed" или "mark_unprocessed"

class BackCallback(CallbackData, prefix="back"):
    to: str  # "vacancies", "applications" или "unprocessed"
    vacancy_id: int = 0  # Для возврата к приложениям конкретной вакансии

class DeleteCallback(CallbackData, prefix="delete"):
    application_id: int
    action: str  # "confirm" или "cancel"
    source: str = "recent"  # Откуда пришел пользователь

class SummaryCallback(CallbackData, prefix="summary"):
    application_id: int
    action: str  # "generate"

class ResumeCallback(CallbackData, prefix="resume"):
    application_id: int
    action: str  # "download"

class AccountCallback(CallbackData, prefix="account"):
    account_id: str

class AccountToggleCallback(CallbackData, prefix="account_toggle"):
    account_id: str
    action: str  # "enable" или "disable"

async def delete_message_after_delay(message, delay_seconds):
    """Удаляет сообщение через указанное количество секунд"""
    import asyncio
    await asyncio.sleep(delay_seconds)
    try:
        await message.delete()
    except Exception:
        pass  # Игнорируем ошибки если сообщение уже удалено

def clean_html_tags(text):
    """Удаляет HTML теги и эмодзи из текста для Excel"""
    if not text:
        return ""

    import re
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Удаляем эмодзи (базовые)
    text = re.sub(r'[📋👤📧📱🔗📝🛠⏰🎓⚠️📊🤖📄]', '', text)
    # Заменяем множественные пробелы на одинарные
    text = re.sub(r'\s+', ' ', text)
    # Убираем пробелы в начале и конце
    text = text.strip()
    return text

def setup_handlers(dp: Dispatcher):

    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

        # Создаем клавиатуру с командами
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/recent"), KeyboardButton(text="/unprocessed")],
                [KeyboardButton(text="/parse"), KeyboardButton(text="/stats")],
                [KeyboardButton(text="/accounts"), KeyboardButton(text="/add_account")],
                [KeyboardButton(text="/export")]
            ],
            resize_keyboard=True
        )

        await message.answer("Привет! Я HR-бот для обработки откликов на вакансии из Gmail.\n\n"
                           "Команды:\n"
                           "/start - Это сообщение\n"
                           "/stats - Статистика по откликам\n"
                           "/recent - Последние отклики\n"
                           "/unprocessed - Все необработанные отклики\n"
                           "/parse - Парсить новые письма\n"
                           "/export - Экспорт откликов в Excel\n"
                           "/accounts - Управление Gmail аккаунтами\n"
                           "/add_account - Добавить новый Gmail аккаунт",
                           reply_markup=keyboard)

    @dp.message(Command("stats"))
    async def stats_handler(message: Message) -> None:
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            total = await session.execute(text("SELECT COUNT(*) FROM applications WHERE deleted_at IS NULL"))
            total_count = total.scalar()

            processed = await session.execute(text("SELECT COUNT(*) FROM applications WHERE is_processed = true AND deleted_at IS NULL"))
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
                # Считаем количество откликов для каждой вакансии (исключаем удаленные)
                count_stmt = select(Application).where(Application.vacancy_id == vacancy.id, Application.deleted_at.is_(None))
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
        status_msg = await message.answer("🔄 Начинаю парсинг новых писем из всех аккаунтов...")

        try:
            import json
            import os
            from bot.gmail_parser import GmailParser

            # Загружаем конфигурацию аккаунтов
            accounts_config_path = "bot/gmail_accounts.json"
            parsers = []

            if os.path.exists(accounts_config_path):
                with open(accounts_config_path, 'r', encoding='utf-8') as f:
                    accounts = json.load(f)

                for account in accounts:
                    if account.get('enabled', True):
                        parser = GmailParser(
                            account_id=account['id'],
                            credentials_path=account['credentials_path'],
                            token_path=account['token_path']
                        )
                        parsers.append(parser)
            else:
                # Если конфига нет, используем дефолтный аккаунт
                parsers = [GmailParser()]

            # Парсим новые письма из всех аккаунтов
            total_parsed = 0
            all_new_vacancies = []

            for parser in parsers:
                result = await parser.parse_new_emails()
                total_parsed += result["parsed_count"]

                if result["new_vacancies"]:
                    all_new_vacancies.extend(result["new_vacancies"])

            if total_parsed > 0:
                text = f"✅ Парсинг завершен!\nОбработано новых откликов: <b>{total_parsed}</b>"

                if all_new_vacancies:
                    unique_vacancies = list(set(all_new_vacancies))
                    text += f"\n\n<b>Новые вакансии ({len(unique_vacancies)}):</b>"
                    for vacancy in unique_vacancies:
                        text += f"\n• {vacancy}"

                await status_msg.edit_text(text, parse_mode="HTML")
            else:
                await status_msg.edit_text("📭 Новых писем не найдено")

            # Удаляем сообщения через 2 секунды
            import asyncio
            asyncio.create_task(delete_message_after_delay(status_msg, 2))
            asyncio.create_task(delete_message_after_delay(message, 2))

        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка при парсинге: {str(e)}")
            # Удаляем сообщения с ошибкой через 2 секунды
            import asyncio
            asyncio.create_task(delete_message_after_delay(status_msg, 2))
            asyncio.create_task(delete_message_after_delay(message, 2))

    @dp.message(Command("unprocessed"))
    async def unprocessed_handler(message: Message) -> None:
        async with AsyncSessionLocal() as session:
            # Получаем все необработанные отклики с вакансиями (исключаем удаленные)
            from sqlalchemy.orm import selectinload
            stmt = select(Application).options(selectinload(Application.vacancy)).where(Application.is_processed == False, Application.deleted_at.is_(None)).order_by(desc(Application.created_at))
            result = await session.execute(stmt)
            unprocessed_applications = result.scalars().all()

            if not unprocessed_applications:
                await message.answer("✅ Все отклики обработаны!")
                return

            # Создаем клавиатуру с необработанными откликами
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])

            for app in unprocessed_applications:
                # Формируем текст кнопки: {имя} - {телефон} - {email}
                button_text = app.name
                if app.phone:
                    button_text += f" - {app.phone}"
                if app.email:
                    button_text += f" - {app.email}"

                # Добавляем эмодзи для необработанных
                button_text = f"❌ {button_text}"

                button = InlineKeyboardButton(
                    text=button_text,
                    callback_data=ApplicationCallback(application_id=app.id, source="unprocessed").pack()
                )
                keyboard.inline_keyboard.append([button])

            text = f"❌ <b>Необработанные отклики ({len(unprocessed_applications)}):</b>\n\n"
            text += "Выберите отклик для просмотра и обработки:"

            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

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

            # Получаем отклики на эту вакансию (исключаем удаленные)
            apps_stmt = select(Application).where(Application.vacancy_id == callback_data.vacancy_id, Application.deleted_at.is_(None)).order_by(desc(Application.created_at))
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
                    callback_data=ApplicationCallback(application_id=app.id, source="vacancy").pack()
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
            # Добавляем кнопку удаления
            delete_button = InlineKeyboardButton(
                text="🗑️ Удалить отклик",
                callback_data=DeleteCallback(application_id=application.id, action="confirm", source=callback_data.source).pack()
            )
            keyboard.inline_keyboard.append([process_button, delete_button])

            # Добавляем кнопки для работы с резюме если есть файл
            if (application.file_path or application.attachment_filename) and (
                application.attachment_filename and
                (application.attachment_filename.lower().endswith('.pdf') or application.attachment_filename.lower().endswith('.docx'))
            ):
                # Кнопка для работы с summary
                if application.summary:
                    # Если summary уже есть - показываем кнопку для отправки
                    summary_button = InlineKeyboardButton(
                        text="📊 Показать анализ резюме",
                        callback_data=SummaryCallback(application_id=application.id, action="show").pack()
                    )
                else:
                    # Если summary нет - показываем кнопку для генерации
                    summary_button = InlineKeyboardButton(
                        text="🤖 Сгенерировать анализ резюме",
                        callback_data=SummaryCallback(application_id=application.id, action="generate").pack()
                    )
                keyboard.inline_keyboard.append([summary_button])

                # Кнопка получения файла резюме
                resume_button = InlineKeyboardButton(
                    text="📄 Получить файл резюме",
                    callback_data=ResumeCallback(application_id=application.id, action="download").pack()
                )
                keyboard.inline_keyboard.append([resume_button])

            # Добавляем кнопку "Назад" в зависимости от источника
            if callback_data.source == "unprocessed":
                back_button = InlineKeyboardButton(
                    text="⬅️ Назад к необработанным",
                    callback_data=BackCallback(to="unprocessed").pack()
                )
            elif callback_data.source == "vacancy":
                back_button = InlineKeyboardButton(
                    text="⬅️ Назад к откликам",
                    callback_data=BackCallback(to="applications", vacancy_id=application.vacancy_id).pack()
                )
            else:  # source == "recent" или другое
                back_button = InlineKeyboardButton(
                    text="⬅️ Назад к вакансиям",
                    callback_data=BackCallback(to="vacancies").pack()
                )
            keyboard.inline_keyboard.append([back_button])

            # Отправляем сообщение с информацией
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)

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
            # Добавляем кнопку удаления
            delete_button = InlineKeyboardButton(
                text="🗑️ Удалить отклик",
                callback_data=DeleteCallback(application_id=application.id, action="confirm", source="vacancy").pack()
            )
            keyboard.inline_keyboard.append([process_button, delete_button])

            # Получаем source из исходного callback (нужно передать через ProcessCallback)
            # Пока используем applications как fallback
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

    @dp.callback_query(DeleteCallback.filter())
    async def delete_handler(query: CallbackQuery, callback_data: DeleteCallback) -> None:
        await query.answer()

        if callback_data.action == "confirm":
            # Показываем подтверждение удаления
            async with AsyncSessionLocal() as session:
                app_stmt = select(Application).where(Application.id == callback_data.application_id)
                app_result = await session.execute(app_stmt)
                application = app_result.scalar_one_or_none()

                if not application:
                    await query.message.edit_text("❌ Отклик не найден")
                    return

                # Создаем клавиатуру подтверждения
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Да, удалить",
                            callback_data=DeleteCallback(application_id=application.id, action="execute", source=callback_data.source).pack()
                        ),
                        InlineKeyboardButton(
                            text="❌ Отмена",
                            callback_data=DeleteCallback(application_id=application.id, action="cancel", source=callback_data.source).pack()
                        )
                    ]
                ])

                text = f"⚠️ <b>Подтверждение удаления</b>\n\n"
                text += f"Вы действительно хотите удалить отклик?\n\n"
                text += f"👤 <b>{application.name}</b>\n"
                if application.email:
                    text += f"📧 {application.email}\n"
                if application.phone:
                    text += f"📱 {application.phone}\n"
                text += f"\n❗ <b>Это действие нельзя отменить!</b>"

                await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

        elif callback_data.action == "execute":
            # Удаляем сообщение с файлом резюме если оно есть
            user_id = query.from_user.id
            if user_id in user_resume_messages:
                try:
                    await query.bot.delete_message(chat_id=query.message.chat.id, message_id=user_resume_messages[user_id])
                except Exception:
                    pass  # Игнорируем ошибки если сообщение уже удалено
                del user_resume_messages[user_id]

            # Выполняем удаление
            async with AsyncSessionLocal() as session:
                app_stmt = select(Application).where(Application.id == callback_data.application_id)
                app_result = await session.execute(app_stmt)
                application = app_result.scalar_one_or_none()

                if not application:
                    await query.message.edit_text("❌ Отклик не найден")
                    return

                # Удаляем файл если он существует
                if application.file_path and os.path.exists(application.file_path):
                    try:
                        os.remove(application.file_path)
                        print(f"Удален файл: {application.file_path}")
                    except Exception as e:
                        print(f"Ошибка удаления файла: {e}")

                # Используем soft delete вместо удаления из базы данных
                from datetime import datetime
                application.deleted_at = datetime.now()
                await session.commit()

                # Показываем уведомление об удалении
                await query.message.edit_text(
                    f"✅ Отклик от <b>{application.name}</b> успешно удален",
                    parse_mode="HTML"
                )

                # Ждем 1 секунду и возвращаемся к соответствующему меню
                import asyncio
                await asyncio.sleep(1)

                # Возвращаемся к соответствующему меню в зависимости от источника
                if callback_data.source == "unprocessed":
                    # Возвращаемся к списку необработанных откликов
                    async with AsyncSessionLocal() as session:
                        from sqlalchemy.orm import selectinload
                        stmt = select(Application).options(selectinload(Application.vacancy)).where(Application.is_processed == False, Application.deleted_at.is_(None)).order_by(desc(Application.created_at))
                        result = await session.execute(stmt)
                        unprocessed_applications = result.scalars().all()

                        if not unprocessed_applications:
                            await query.message.edit_text("✅ Все отклики обработаны!", parse_mode="HTML")
                            return

                        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

                        for app in unprocessed_applications:
                            button_text = app.name
                            if app.phone:
                                button_text += f" - {app.phone}"
                            if app.email:
                                button_text += f" - {app.email}"

                            button_text = f"❌ {button_text}"

                            button = InlineKeyboardButton(
                                text=button_text,
                                callback_data=ApplicationCallback(application_id=app.id, source="unprocessed").pack()
                            )
                            keyboard.inline_keyboard.append([button])

                        text = f"❌ <b>Необработанные отклики ({len(unprocessed_applications)}):</b>\n\n"
                        text += "Выберите отклик для просмотра и обработки:"

                        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

                elif callback_data.source == "vacancy":
                    # Возвращаемся к списку откликов вакансии
                    back_callback = BackCallback(to="applications", vacancy_id=application.vacancy_id)
                    await back_handler(query, back_callback)

                else:  # source == "recent" или другое
                    # Возвращаемся к списку вакансий
                    back_callback = BackCallback(to="vacancies")
                    await back_handler(query, back_callback)

        elif callback_data.action == "cancel":
            # Отменяем удаление - возвращаемся к детальному просмотру
            application_callback = ApplicationCallback(application_id=callback_data.application_id, source=callback_data.source)
            await application_details_handler(query, application_callback)

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
                    count_stmt = select(Application).where(Application.vacancy_id == vacancy.id, Application.deleted_at.is_(None))
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

                apps_stmt = select(Application).where(Application.vacancy_id == callback_data.vacancy_id, Application.deleted_at.is_(None)).order_by(desc(Application.created_at))
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

        elif callback_data.to == "unprocessed":
            # Возвращаемся к списку необработанных откликов
            async with AsyncSessionLocal() as session:
                from sqlalchemy.orm import selectinload
                stmt = select(Application).options(selectinload(Application.vacancy)).where(Application.is_processed == False, Application.deleted_at.is_(None)).order_by(desc(Application.created_at))
                result = await session.execute(stmt)
                unprocessed_applications = result.scalars().all()

                if not unprocessed_applications:
                    await query.message.edit_text("✅ Все отклики обработаны!")
                    return

                keyboard = InlineKeyboardMarkup(inline_keyboard=[])

                for app in unprocessed_applications:
                    button_text = app.name
                    if app.phone:
                        button_text += f" - {app.phone}"
                    if app.email:
                        button_text += f" - {app.email}"

                    button_text = f"❌ {button_text}"

                    button = InlineKeyboardButton(
                        text=button_text,
                        callback_data=ApplicationCallback(application_id=app.id, source="unprocessed").pack()
                    )
                    keyboard.inline_keyboard.append([button])

                text = f"❌ <b>Необработанные отклики ({len(unprocessed_applications)}):</b>\n\n"
                text += "Выберите отклик для просмотра и обработки:"

                await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.message(Command("export"))
    async def export_handler(message: Message) -> None:
        status_msg = await message.answer("📊 Создаю Excel файл с откликами...")

        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy.orm import selectinload

                # Получаем все не удаленные отклики с вакансиями
                stmt = select(Application).options(selectinload(Application.vacancy)).where(
                    Application.deleted_at.is_(None)
                ).order_by(desc(Application.created_at))
                result = await session.execute(stmt)
                applications = result.scalars().all()

                if not applications:
                    await status_msg.edit_text("📭 Нет откликов для экспорта")
                    import asyncio
                    asyncio.create_task(delete_message_after_delay(status_msg, 2))
                    asyncio.create_task(delete_message_after_delay(message, 2))
                    return

                # Создаем Excel файл
                from openpyxl import Workbook
                from openpyxl.styles import Font, PatternFill, Alignment
                from datetime import datetime

                wb = Workbook()
                ws = wb.active
                ws.title = "Отклики на вакансии"

                # Заголовки
                headers = [
                    "ID", "Имя", "Email", "Телефон", "Вакансия",
                    "Статус", "Дата отклика", "Сообщение", "Файл", "Анализ резюме"
                ]

                # Стиль заголовков
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

                for col, header in enumerate(headers, 1):
                    cell = ws.cell(row=1, column=col, value=header)
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = Alignment(horizontal="center")

                # Данные
                for row, app in enumerate(applications, 2):
                    ws.cell(row=row, column=1, value=app.id)
                    ws.cell(row=row, column=2, value=app.name or "")
                    ws.cell(row=row, column=3, value=app.email or "")
                    ws.cell(row=row, column=4, value=app.phone or "")
                    ws.cell(row=row, column=5, value=app.vacancy.title if app.vacancy else "")
                    ws.cell(row=row, column=6, value="Обработан" if app.is_processed else "Не обработан")
                    ws.cell(row=row, column=7, value=app.created_at.strftime('%d.%m.%Y %H:%M') if app.created_at else "")

                    # Колонка "Сообщение" с переносом текста
                    message_cell = ws.cell(row=row, column=8, value=app.applicant_message or "")
                    message_cell.alignment = Alignment(wrap_text=True, vertical="top")

                    ws.cell(row=row, column=9, value=app.attachment_filename or "")

                    # Колонка "Анализ резюме" с очищенным от HTML текстом
                    summary_text = clean_html_tags(app.summary) if app.summary else ""
                    summary_cell = ws.cell(row=row, column=10, value=summary_text)
                    summary_cell.alignment = Alignment(wrap_text=True, vertical="top")

                # Автоширина колонок
                for column in ws.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    ws.column_dimensions[column_letter].width = adjusted_width

                # Сохраняем файл
                filename = f"отклики_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                file_path = f"exports/{filename}"

                # Создаем директорию если её нет
                import os
                os.makedirs("exports", exist_ok=True)

                wb.save(file_path)

                # Отправляем файл
                from aiogram.types import FSInputFile
                file = FSInputFile(file_path, filename=filename)

                await status_msg.edit_text(f"✅ Excel файл готов!\nОтклики: {len(applications)}")
                await message.answer_document(
                    file,
                    caption=f"📊 Экспорт откликов\n\n"
                           f"Всего откликов: {len(applications)}\n"
                           f"Создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )

                # Удаляем временный файл
                try:
                    os.remove(file_path)
                except:
                    pass

                # Удаляем сообщения через 2 секунды
                import asyncio
                asyncio.create_task(delete_message_after_delay(status_msg, 2))
                asyncio.create_task(delete_message_after_delay(message, 2))

        except Exception as e:
            await status_msg.edit_text(f"❌ Ошибка создания Excel: {str(e)}")
            import asyncio
            asyncio.create_task(delete_message_after_delay(status_msg, 2))
            asyncio.create_task(delete_message_after_delay(message, 2))

    @dp.callback_query(SummaryCallback.filter())
    async def summary_handler(query: CallbackQuery, callback_data: SummaryCallback) -> None:
        await query.answer()

        if callback_data.action == "show":
            # Показываем готовый summary
            async with AsyncSessionLocal() as session:
                # Получаем отклик
                app_stmt = select(Application).where(Application.id == callback_data.application_id)
                app_result = await session.execute(app_stmt)
                application = app_result.scalar_one_or_none()

                if not application:
                    await query.message.answer("❌ Отклик не найден")
                    return

                if application.summary:
                    # Отправляем готовый summary
                    summary_msg = f"📊 <b>Анализ резюме для {application.name}:</b>\n\n{application.summary}"
                    await query.message.answer(summary_msg, parse_mode="HTML")
                else:
                    await query.message.answer("❌ Анализ резюме не найден")

        elif callback_data.action == "generate":
            status_msg = await query.message.answer("🤖 Генерирую анализ резюме...")

            try:
                async with AsyncSessionLocal() as session:
                    # Получаем отклик
                    app_stmt = select(Application).where(Application.id == callback_data.application_id)
                    app_result = await session.execute(app_stmt)
                    application = app_result.scalar_one_or_none()

                    if not application:
                        await status_msg.edit_text("❌ Отклик не найден")
                        return

                    # Получаем вакансию
                    vacancy_stmt = select(Vacancy).where(Vacancy.id == application.vacancy_id)
                    vacancy_result = await session.execute(vacancy_stmt)
                    vacancy = vacancy_result.scalar_one_or_none()

                    # Создаем сервис для генерации summary
                    summary_service = ResumeSummaryService()

                    # Генерируем summary
                    summary = await summary_service.generate_summary_for_application(application, vacancy)

                    if summary:
                        # Сохраняем summary в базу данных
                        application.summary = summary
                        await session.commit()

                        await status_msg.edit_text("✅ Анализ резюме сгенерирован!")

                        # Отправляем сгенерированный summary
                        summary_msg = f"🤖 <b>Анализ резюме для {application.name}:</b>\n\n{summary}"
                        await query.message.answer(summary_msg, parse_mode="HTML")

                        # Удаляем статусное сообщение через 2 секунды
                        import asyncio
                        asyncio.create_task(delete_message_after_delay(status_msg, 2))

                    else:
                        await status_msg.edit_text("❌ Не удалось сгенерировать анализ резюме")
                        import asyncio
                        asyncio.create_task(delete_message_after_delay(status_msg, 3))

            except Exception as e:
                await status_msg.edit_text(f"❌ Ошибка при генерации анализа: {str(e)}")
                import asyncio
                asyncio.create_task(delete_message_after_delay(status_msg, 3))

    @dp.callback_query(ResumeCallback.filter())
    async def resume_handler(query: CallbackQuery, callback_data: ResumeCallback) -> None:
        await query.answer()

        if callback_data.action == "download":
            async with AsyncSessionLocal() as session:
                # Получаем отклик
                app_stmt = select(Application).where(Application.id == callback_data.application_id)
                app_result = await session.execute(app_stmt)
                application = app_result.scalar_one_or_none()

                if not application:
                    await query.message.answer("❌ Отклик не найден")
                    return

                # Отправляем файл если он есть
                user_id = query.from_user.id
                if application.file_path and os.path.exists(application.file_path):
                    try:
                        from aiogram.types import FSInputFile
                        file = FSInputFile(application.file_path, filename=application.attachment_filename)
                        file_msg = await query.message.answer_document(file, caption=f"📄 Резюме от {application.name}")
                        # Сохраняем ID сообщения с файлом
                        user_resume_messages[user_id] = file_msg.message_id
                    except Exception as e:
                        error_msg = await query.message.answer(f"❌ Ошибка при отправке файла: {str(e)}")
                        user_resume_messages[user_id] = error_msg.message_id
                elif application.file_url:
                    url_msg = await query.message.answer(f"📄 Файл резюме доступен по ссылке: {application.file_url}")
                    user_resume_messages[user_id] = url_msg.message_id
                else:
                    await query.message.answer("❌ Файл резюме не найден")

    @dp.message(Command("accounts"))
    async def accounts_handler(message: Message) -> None:
        """Показывает список всех Gmail аккаунтов"""
        import json
        import os

        accounts_config_path = "bot/gmail_accounts.json"

        if not os.path.exists(accounts_config_path):
            await message.answer("❌ Файл конфигурации аккаунтов не найден")
            return

        with open(accounts_config_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)

        if not accounts:
            await message.answer("📭 Нет настроенных Gmail аккаунтов\n\n"
                               "Используйте скрипт add_gmail_account.py для добавления")
            return

        # Создаем клавиатуру с аккаунтами
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for account in accounts:
            status_emoji = "✅" if account.get('enabled', True) else "❌"
            button_text = f"{status_emoji} {account.get('name', account['id'])}"

            button = InlineKeyboardButton(
                text=button_text,
                callback_data=AccountCallback(account_id=account['id']).pack()
            )
            keyboard.inline_keyboard.append([button])

        text = "📧 <b>Gmail аккаунты</b>\n\n"
        text += f"Всего аккаунтов: <b>{len(accounts)}</b>\n"
        enabled_count = sum(1 for acc in accounts if acc.get('enabled', True))
        text += f"Активных: <b>{enabled_count}</b>\n\n"
        text += "Выберите аккаунт для просмотра деталей:"

        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.callback_query(AccountCallback.filter())
    async def account_details_handler(query: CallbackQuery, callback_data: AccountCallback) -> None:
        """Показывает детали конкретного аккаунта"""
        await query.answer()

        import json
        import os

        accounts_config_path = "bot/gmail_accounts.json"

        with open(accounts_config_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)

        # Находим аккаунт
        account = None
        for acc in accounts:
            if acc['id'] == callback_data.account_id:
                account = acc
                break

        if not account:
            await query.message.edit_text("❌ Аккаунт не найден")
            return

        # Формируем детальную информацию
        is_enabled = account.get('enabled', True)
        status_emoji = "✅" if is_enabled else "❌"
        status_text = "Активен" if is_enabled else "Отключен"

        text = f"📧 <b>{account.get('name', account['id'])}</b>\n\n"
        text += f"🆔 <b>ID:</b> <code>{account['id']}</code>\n"
        text += f"🏷️ <b>Статус:</b> {status_emoji} {status_text}\n\n"

        text += f"📂 <b>Файлы:</b>\n"
        text += f"   • Credentials: <code>{account.get('credentials_path', 'Не указано')}</code>\n"
        text += f"   • Token: <code>{account.get('token_path', 'Не указано')}</code>\n"

        # Создаем кнопки управления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        if is_enabled:
            toggle_button = InlineKeyboardButton(
                text="❌ Отключить аккаунт",
                callback_data=AccountToggleCallback(account_id=account['id'], action="disable").pack()
            )
        else:
            toggle_button = InlineKeyboardButton(
                text="✅ Включить аккаунт",
                callback_data=AccountToggleCallback(account_id=account['id'], action="enable").pack()
            )

        keyboard.inline_keyboard.append([toggle_button])

        # Кнопка "Назад"
        back_button = InlineKeyboardButton(
            text="⬅️ Назад к списку",
            callback_data="back_to_accounts"
        )
        keyboard.inline_keyboard.append([back_button])

        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.callback_query(AccountToggleCallback.filter())
    async def account_toggle_handler(query: CallbackQuery, callback_data: AccountToggleCallback) -> None:
        """Включает или отключает аккаунт"""
        await query.answer()

        import json

        accounts_config_path = "bot/gmail_accounts.json"

        with open(accounts_config_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)

        # Находим и обновляем аккаунт
        account_updated = False
        for account in accounts:
            if account['id'] == callback_data.account_id:
                if callback_data.action == "enable":
                    account['enabled'] = True
                    status_msg = f"✅ Аккаунт <b>{account.get('name', account['id'])}</b> включен"
                else:
                    account['enabled'] = False
                    status_msg = f"❌ Аккаунт <b>{account.get('name', account['id'])}</b> отключен"
                account_updated = True
                break

        if not account_updated:
            await query.message.answer("❌ Аккаунт не найден")
            return

        # Сохраняем изменения
        with open(accounts_config_path, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)

        # Показываем уведомление
        notification = await query.message.answer(status_msg, parse_mode="HTML")

        # Обновляем детали аккаунта
        account_callback = AccountCallback(account_id=callback_data.account_id)
        await account_details_handler(query, account_callback)

        # Удаляем уведомление через 2 секунды
        import asyncio
        asyncio.create_task(delete_message_after_delay(notification, 2))

    @dp.callback_query(lambda c: c.data == "back_to_accounts")
    async def back_to_accounts_handler(query: CallbackQuery) -> None:
        """Возвращается к списку аккаунтов"""
        await query.answer()

        import json
        import os

        accounts_config_path = "bot/gmail_accounts.json"

        with open(accounts_config_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)

        # Создаем клавиатуру с аккаунтами
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for account in accounts:
            status_emoji = "✅" if account.get('enabled', True) else "❌"
            button_text = f"{status_emoji} {account.get('name', account['id'])}"

            button = InlineKeyboardButton(
                text=button_text,
                callback_data=AccountCallback(account_id=account['id']).pack()
            )
            keyboard.inline_keyboard.append([button])

        text = "📧 <b>Gmail аккаунты</b>\n\n"
        text += f"Всего аккаунтов: <b>{len(accounts)}</b>\n"
        enabled_count = sum(1 for acc in accounts if acc.get('enabled', True))
        text += f"Активных: <b>{enabled_count}</b>\n\n"
        text += "Выберите аккаунт для просмотра деталей:"

        await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

    # Словарь для хранения состояния авторизации пользователей
    user_auth_states = {}

    @dp.message(Command("add_account"))
    async def add_account_command_handler(message: Message) -> None:
        """Добавляет новый Gmail аккаунт через OAuth"""
        from bot.gmail_account_manager import GmailAccountManager

        try:
            # Генерируем OAuth URL
            success, auth_url, flow_data = GmailAccountManager.generate_auth_url()

            if not success:
                await message.answer(auth_url, parse_mode="HTML")
                return

            # Сохраняем состояние ожидания кода для этого пользователя
            user_auth_states[message.from_user.id] = True

            auth_msg = (
                "🔐 <b>Добавление нового Gmail аккаунта</b>\n\n"
                "1️⃣ Перейдите по ссылке ниже для авторизации:\n"
                f"<a href='{auth_url}'>Открыть страницу авторизации Google</a>\n\n"
                "2️⃣ Выберите Gmail аккаунт и разрешите доступ\n\n"
                "3️⃣ Скопируйте код авторизации\n\n"
                "4️⃣ Отправьте мне этот код следующим сообщением\n\n"
                "💡 Код начинается с <code>4/</code> и выглядит примерно так:\n"
                "<code>4/0Adeu5BW...</code>"
            )

            await message.answer(auth_msg, parse_mode="HTML", disable_web_page_preview=True)

        except Exception as e:
            error_text = (
                f"❌ <b>Ошибка генерации ссылки</b>\n\n"
                f"<code>{str(e)}</code>\n\n"
                f"💡 Убедитесь, что credentials.json находится в gmail_tokens/"
            )
            await message.answer(error_text, parse_mode="HTML")

    @dp.message(lambda message: message.from_user.id in user_auth_states and user_auth_states.get(message.from_user.id))
    async def handle_auth_code(message: Message) -> None:
        """Обрабатывает код авторизации от пользователя"""
        from bot.gmail_account_manager import GmailAccountManager

        auth_code = message.text.strip()

        # Проверяем что это похоже на код авторизации
        if not auth_code.startswith('4/'):
            await message.answer(
                "⚠️ Это не похоже на код авторизации.\n\n"
                "Код должен начинаться с <code>4/</code>\n"
                "Попробуйте еще раз или отправьте /cancel для отмены.",
                parse_mode="HTML"
            )
            return

        status_msg = await message.answer("⏳ Проверяю код авторизации...")

        try:
            # Завершаем авторизацию с кодом
            success, msg, account_data = GmailAccountManager.complete_auth_with_code(auth_code)

            # Убираем состояние ожидания кода
            del user_auth_states[message.from_user.id]

            if success:
                # Успешно добавлен
                final_text = (
                    "✅ <b>Новый аккаунт успешно добавлен!</b>\n\n"
                    f"📧 <b>Email:</b> <code>{account_data['name']}</code>\n"
                    f"🆔 <b>ID:</b> <code>{account_data['id']}</code>\n"
                    f"🏷️ <b>Статус:</b> ❌ Отключен\n\n"
                    "💡 <b>Следующие шаги:</b>\n"
                    "1. Используйте /accounts\n"
                    "2. Выберите этот аккаунт\n"
                    "3. Нажмите \"✅ Включить аккаунт\""
                )
                await status_msg.edit_text(final_text, parse_mode="HTML")
            else:
                # Ошибка
                await status_msg.edit_text(msg, parse_mode="HTML")

            # Удаляем сообщение с кодом (для безопасности)
            import asyncio
            asyncio.create_task(delete_message_after_delay(message, 1))

        except Exception as e:
            # Убираем состояние ожидания кода
            if message.from_user.id in user_auth_states:
                del user_auth_states[message.from_user.id]

            error_text = (
                f"❌ <b>Ошибка авторизации</b>\n\n"
                f"<code>{str(e)}</code>\n\n"
                f"💡 Попробуйте еще раз: /add_account"
            )
            await status_msg.edit_text(error_text, parse_mode="HTML")

            # Удаляем сообщение с кодом
            import asyncio
            asyncio.create_task(delete_message_after_delay(message, 1))

    @dp.message(Command("cancel"))
    async def cancel_handler(message: Message) -> None:
        """Отменяет текущую операцию"""
        user_id = message.from_user.id

        if user_id in user_auth_states:
            del user_auth_states[user_id]
            await message.answer("✅ Операция отменена")
        else:
            await message.answer("❌ Нет активных операций для отмены")
