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
                           "/unprocessed - Все необработанные отклики\n"
                           "/parse - Парсить новые письма\n"
                           "/export - Экспорт откликов в Excel")

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
        status_msg = await message.answer("🔄 Начинаю парсинг новых писем...")

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
            # Добавляем кнопку удаления
            delete_button = InlineKeyboardButton(
                text="🗑️ Удалить отклик",
                callback_data=DeleteCallback(application_id=application.id, action="confirm", source=callback_data.source).pack()
            )
            keyboard.inline_keyboard.append([process_button, delete_button])

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
                    "Статус", "Дата отклика", "Сообщение", "Файл"
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