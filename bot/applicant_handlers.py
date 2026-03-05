from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from sqlalchemy import select
import os
import uuid

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Vacancy, Application
from shared.models.user import TelegramUser

user_application_states = {}

class VacancyApplyCallback(CallbackData, prefix="vapply"):
    vacancy_id: int

class ApplicationStepCallback(CallbackData, prefix="appstep"):
    action: str

def setup_applicant_handlers(dp: Dispatcher):

    @dp.message(F.text == "💼 Вакансии")
    async def show_vacancies_button(message: Message):
        await show_vacancies_list(message)

    async def show_vacancies_list(message: Message):
        async with AsyncSessionLocal() as session:
            stmt = select(Vacancy).where(Vacancy.is_active == True).order_by(Vacancy.created_at.desc())
            result = await session.execute(stmt)
            vacancies = result.scalars().all()

            if not vacancies:
                user_stmt = select(TelegramUser).where(TelegramUser.telegram_id == message.from_user.id)
                user_result = await session.execute(user_stmt)
                user = user_result.scalar_one_or_none()

                keyboard = None
                if user and (user.is_admin or user.is_moderator):
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Создать вакансию", callback_data="create_new_vacancy")]
                    ])

                await message.answer("К сожалению, сейчас нет активных вакансий.", reply_markup=keyboard)
                return

            text = "📋 <b>Активные вакансии:</b>\n\n"

            keyboard_buttons = []
            for vacancy in vacancies[:10]:
                text += f"• <b>{vacancy.title}</b>\n"
                if vacancy.description:
                    desc = vacancy.description[:100] + "..." if len(vacancy.description) > 100 else vacancy.description
                    text += f"  {desc}\n"
                text += "\n"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"📝 Откликнуться на: {vacancy.title}",
                        callback_data=VacancyApplyCallback(vacancy_id=vacancy.id).pack()
                    )
                ])

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.callback_query(VacancyApplyCallback.filter())
    async def start_application(query: CallbackQuery, callback_data: VacancyApplyCallback, user: TelegramUser):
        await query.answer()

        async with AsyncSessionLocal() as session:
            vacancy = await session.get(Vacancy, callback_data.vacancy_id)
            if not vacancy or not vacancy.is_active:
                await query.message.answer("❌ Эта вакансия больше недоступна.")
                return

            existing_app_stmt = select(Application).where(
                Application.vacancy_id == vacancy.id,
                Application.telegram_user_id == user.telegram_id,
                Application.application_source == "telegram",
                Application.deleted_at.is_(None)
            )
            existing_app_result = await session.execute(existing_app_stmt)
            existing_app = existing_app_result.scalar_one_or_none()

            if existing_app:
                await query.message.answer(
                    f"⚠️ Вы уже откликались на вакансию <b>{vacancy.title}</b>\n\n"
                    f"📅 Дата отклика: {existing_app.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                    "Мы рассмотрим ваш отклик и свяжемся с вами.",
                    parse_mode="HTML"
                )
                return

            user_application_states[user.telegram_id] = {
                "vacancy_id": vacancy.id,
                "vacancy_title": vacancy.title,
                "step": "name"
            }

            text = f"""
📝 <b>Отклик на вакансию: {vacancy.title}</b>

Пожалуйста, ответьте на несколько вопросов:

<b>Шаг 1/4:</b> Как вас зовут? (ФИО)
"""

            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить", callback_data=ApplicationStepCallback(action="cancel").pack())]
            ])

            await query.message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

    @dp.message(lambda message: message.from_user.id in user_application_states and message.text and not message.text.startswith('/'))
    async def handle_application_step(message: Message):
        user_id = message.from_user.id
        state = user_application_states.get(user_id)

        if not state:
            return

        step = state["step"]

        if step == "name":
            state["name"] = message.text
            state["step"] = "email"

            text = """
<b>Шаг 2/4:</b> Укажите ваш email для связи

Например: ivan@example.com
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить", callback_data=ApplicationStepCallback(action="cancel").pack())]
            ])
            await message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

        elif step == "email":
            if '@' not in message.text or '.' not in message.text:
                await message.answer("⚠️ Пожалуйста, введите корректный email адрес.")
                return

            state["email"] = message.text
            state["step"] = "phone"

            text = """
<b>Шаг 3/4:</b> Укажите ваш телефон для связи

Например: +992123456789 или 8-999-123-45-67
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить", callback_data=ApplicationStepCallback(action="cancel").pack())]
            ])
            await message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

        elif step == "phone":
            state["phone"] = message.text
            state["step"] = "message"

            text = """
<b>Шаг 4/5:</b> Напишите сопроводительное письмо (по желанию)

Расскажите, почему вы хотите работать у нас, ваш опыт и навыки.

Или отправьте: <code>skip</code> чтобы пропустить
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=ApplicationStepCallback(action="skip_message").pack())],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=ApplicationStepCallback(action="cancel").pack())]
            ])
            await message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

        elif step == "message":
            if message.text.lower() != "skip":
                state["message"] = message.text
            else:
                state["message"] = None

            state["step"] = "resume"

            text = """
<b>Шаг 5/5:</b> Прикрепите ваше резюме (PDF или DOCX)

Или отправьте: <code>skip</code> если нет резюме
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=ApplicationStepCallback(action="skip_resume").pack())],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=ApplicationStepCallback(action="cancel").pack())]
            ])
            await message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

        elif step == "resume":
            if message.text.lower() == "skip":
                state["file_path"] = None
                state["attachment_filename"] = None
                await save_application(message, state, user_id)
            else:
                await message.answer("⚠️ Пожалуйста, прикрепите файл резюме или нажмите кнопку 'Пропустить'")

    @dp.message(lambda message: message.from_user.id in user_application_states and message.document)
    async def handle_resume_upload(message: Message):
        user_id = message.from_user.id
        state = user_application_states.get(user_id)

        if not state or state["step"] != "resume":
            return

        document = message.document

        if not (document.file_name.lower().endswith('.pdf') or document.file_name.lower().endswith('.docx')):
            await message.answer("⚠️ Пожалуйста, отправьте файл в формате PDF или DOCX")
            return

        if document.file_size > 20 * 1024 * 1024:
            await message.answer("⚠️ Размер файла не должен превышать 20 МБ")
            return

        os.makedirs('downloads', exist_ok=True)

        file_id = document.file_id
        file = await message.bot.get_file(file_id)

        unique_filename = f"telegram_{uuid.uuid4().hex[:8]}_{document.file_name}"
        file_path = f"downloads/{unique_filename}"

        await message.bot.download_file(file.file_path, file_path)

        state["file_path"] = file_path
        state["attachment_filename"] = document.file_name

        await save_application(message, state, user_id)

    @dp.callback_query(ApplicationStepCallback.filter())
    async def handle_application_action(query: CallbackQuery, callback_data: ApplicationStepCallback):
        user_id = query.from_user.id
        state = user_application_states.get(user_id)

        if callback_data.action == "cancel":
            if user_id in user_application_states:
                del user_application_states[user_id]
            await query.message.answer("❌ Отклик отменен")
            await query.answer()
            return

        if callback_data.action == "skip_message":
            state["message"] = None
            state["step"] = "resume"

            text = """
<b>Шаг 5/5:</b> Прикрепите ваше резюме (PDF или DOCX)

Или отправьте: <code>skip</code> если нет резюме
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=ApplicationStepCallback(action="skip_resume").pack())],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=ApplicationStepCallback(action="cancel").pack())]
            ])
            await query.message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")
            await query.answer()

        elif callback_data.action == "skip_resume":
            state["file_path"] = None
            state["attachment_filename"] = None
            await save_application(query.message, state, user_id)
            await query.answer()

    async def save_application(message: Message, state: dict, user_id: int):

        try:
            async with AsyncSessionLocal() as session:
                application = Application(
                    name=state["name"],
                    email=state["email"],
                    phone=state["phone"],
                    file_path=state.get("file_path"),
                    attachment_filename=state.get("attachment_filename"),
                    applicant_message=state.get("message"),
                    vacancy_id=state["vacancy_id"],
                    application_source="telegram",
                    telegram_user_id=user_id,
                    gmail_message_id=None
                )

                session.add(application)
                await session.commit()

                success_text = f"""
✅ <b>Ваш отклик успешно отправлен!</b>

<b>Вакансия:</b> {state['vacancy_title']}
<b>Имя:</b> {state['name']}
<b>Email:</b> {state['email']}
<b>Телефон:</b> {state['phone']}

Мы свяжемся с вами в ближайшее время. Спасибо за интерес к нашей компании!
"""

                await message.answer(success_text, parse_mode="HTML")

                del user_application_states[user_id]

        except Exception as e:
            await message.answer(f"❌ Произошла ошибка при отправке отклика: {str(e)}")
            if user_id in user_application_states:
                del user_application_states[user_id]
