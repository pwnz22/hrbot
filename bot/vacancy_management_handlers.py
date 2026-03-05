from aiogram import Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from sqlalchemy import select, desc
import os

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Vacancy, Application
from shared.models.user import TelegramUser
from bot.middleware import moderator_or_admin, admin_only

user_vacancy_creation_states = {}

class VacancyManageCallback(CallbackData, prefix="vmanage"):
    vacancy_id: int
    action: str

class VacancyCreateStepCallback(CallbackData, prefix="vcreate"):
    action: str

def setup_vacancy_management_handlers(dp: Dispatcher):

    @dp.message(Command("vacancies"))
    @moderator_or_admin
    async def list_vacancies_handler(message: Message, user: TelegramUser):
        async with AsyncSessionLocal() as session:
            stmt = select(Vacancy).order_by(desc(Vacancy.created_at))
            result = await session.execute(stmt)
            vacancies = result.scalars().all()

            if not vacancies:
                await message.answer("📋 Пока нет вакансий.\n\nИспользуйте /create_vacancy для создания.")
                return

            text = "📋 <b>Все вакансии:</b>\n\n"

            keyboard_buttons = []
            for vacancy in vacancies:
                status_icon = "✅" if vacancy.is_active else "❌"

                stmt_apps = select(Application).where(Application.vacancy_id == vacancy.id)
                apps_result = await session.execute(stmt_apps)
                apps_count = len(apps_result.scalars().all())

                text += f"{status_icon} <b>{vacancy.title}</b>\n"
                text += f"   📊 Откликов: {apps_count}\n"
                text += f"   📅 Создана: {vacancy.created_at.strftime('%d.%m.%Y')}\n\n"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"⚙️ {vacancy.title}",
                        callback_data=VacancyManageCallback(vacancy_id=vacancy.id, action="view").pack()
                    )
                ])

            keyboard_buttons.append([
                InlineKeyboardButton(text="➕ Создать вакансию", callback_data="create_new_vacancy")
            ])

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

    @dp.message(F.text == "⚙️ Управление вакансиями")
    @moderator_or_admin
    async def text_vacancies_management_handler(message: Message, user: TelegramUser):
        await list_vacancies_handler(message, user)

    @dp.callback_query(F.data == "create_new_vacancy")
    @moderator_or_admin
    async def start_vacancy_creation(query: CallbackQuery, user: TelegramUser):
        await query.answer()

        user_vacancy_creation_states[user.telegram_id] = {
            "step": "title"
        }

        text = """
➕ <b>Создание новой вакансии</b>

<b>Шаг 1/3:</b> Введите название вакансии

Например: Python Developer, QA Engineer, Frontend Developer

[❌ Отменить]
"""
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=VacancyCreateStepCallback(action="cancel").pack())]
        ])

        await query.message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

    @dp.message(Command("create_vacancy"))
    @moderator_or_admin
    async def create_vacancy_command(message: Message, user: TelegramUser):
        user_vacancy_creation_states[user.telegram_id] = {
            "step": "title"
        }

        text = """
➕ <b>Создание новой вакансии</b>

<b>Шаг 1/3:</b> Введите название вакансии

Например: Python Developer, QA Engineer, Frontend Developer
"""
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отменить", callback_data=VacancyCreateStepCallback(action="cancel").pack())]
        ])

        await message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

    @dp.message(lambda message: message.from_user.id in user_vacancy_creation_states and message.text and not message.text.startswith('/'))
    async def handle_vacancy_creation_step(message: Message):
        user_id = message.from_user.id
        state = user_vacancy_creation_states.get(user_id)

        if not state:
            return

        step = state["step"]

        if step == "title":
            state["title"] = message.text
            state["step"] = "description"

            text = """
<b>Шаг 2/3:</b> Введите описание вакансии

Опишите требования, обязанности, условия работы.

Или отправьте: <code>skip</code> чтобы пропустить
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=VacancyCreateStepCallback(action="skip_description").pack())],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=VacancyCreateStepCallback(action="cancel").pack())]
            ])
            await message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

        elif step == "description":
            if message.text.lower() != "skip":
                state["description"] = message.text
            else:
                state["description"] = None

            state["step"] = "requirements"

            text = """
<b>Шаг 3/3:</b> Введите требования к кандидату (опционально)

Например: Python 3+, Django, PostgreSQL, опыт 3+ года

Или отправьте: <code>skip</code> чтобы пропустить
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=VacancyCreateStepCallback(action="skip_requirements").pack())],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=VacancyCreateStepCallback(action="cancel").pack())]
            ])
            await message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")

        elif step == "requirements":
            if message.text.lower() != "skip":
                state["requirements"] = message.text
            else:
                state["requirements"] = None

            await save_vacancy(message, state)

    @dp.callback_query(VacancyCreateStepCallback.filter())
    async def handle_vacancy_create_action(query: CallbackQuery, callback_data: VacancyCreateStepCallback):
        user_id = query.from_user.id
        state = user_vacancy_creation_states.get(user_id)

        if callback_data.action == "cancel":
            if user_id in user_vacancy_creation_states:
                del user_vacancy_creation_states[user_id]
            await query.message.answer("❌ Создание вакансии отменено")
            await query.answer()
            return

        if callback_data.action == "skip_description":
            state["description"] = None
            state["step"] = "requirements"

            text = """
<b>Шаг 3/3:</b> Введите требования к кандидату (опционально)

Например: Python 3+, Django, PostgreSQL, опыт 3+ года

Или отправьте: <code>skip</code> чтобы пропустить
"""
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=VacancyCreateStepCallback(action="skip_requirements").pack())],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=VacancyCreateStepCallback(action="cancel").pack())]
            ])
            await query.message.answer(text, reply_markup=cancel_keyboard, parse_mode="HTML")
            await query.answer()

        elif callback_data.action == "skip_requirements":
            state["requirements"] = None
            await save_vacancy(query.message, state)
            await query.answer()

    async def save_vacancy(message: Message, state: dict):
        user_id = message.from_user.id

        try:
            async with AsyncSessionLocal() as session:
                vacancy = Vacancy(
                    title=state["title"],
                    description=state.get("description"),
                    requirements=state.get("requirements"),
                    is_active=True
                )

                session.add(vacancy)
                await session.commit()
                await session.refresh(vacancy)

                bot_username = (await message.bot.me()).username
                deep_link = f"https://t.me/{bot_username}?start=job_{vacancy.id}"

                success_text = f"""
✅ <b>Вакансия успешно создана!</b>

<b>Название:</b> {state['title']}
<b>ID:</b> {vacancy.id}
<b>Статус:</b> ✅ Активна

<b>Deep link для соискателей:</b>
<code>{deep_link}</code>

Отправьте эту ссылку в соцсетях, на сайте или в мессенджерах!

Управление вакансией: /vacancies
"""
                from urllib.parse import quote
                description = state.get('description', '')
                desc_text = f"\n\n📝 {description}" if description else ""
                share_text = f"🔥 Вакансия: {state['title']}{desc_text}"
                share_url = f"https://t.me/share/url?url={quote(deep_link)}&text={quote(share_text)}"

                share_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📤 Поделиться вакансией", url=share_url)]
                ])

                await message.answer(success_text, reply_markup=share_keyboard, parse_mode="HTML")

                del user_vacancy_creation_states[user_id]

        except Exception as e:
            await message.answer(f"❌ Произошла ошибка при создании вакансии: {str(e)}")
            if user_id in user_vacancy_creation_states:
                del user_vacancy_creation_states[user_id]

    @dp.callback_query(VacancyManageCallback.filter())
    async def vacancy_manage_handler(query: CallbackQuery, callback_data: VacancyManageCallback, user: TelegramUser):
        await query.answer()

        async with AsyncSessionLocal() as session:
            vacancy = await session.get(Vacancy, callback_data.vacancy_id)

            if not vacancy:
                await query.message.answer("❌ Вакансия не найдена")
                return

            if callback_data.action == "view":
                stmt = select(Application).where(Application.vacancy_id == vacancy.id)
                result = await session.execute(stmt)
                applications = result.scalars().all()

                telegram_apps = len([a for a in applications if a.application_source == 'telegram'])
                email_apps = len([a for a in applications if a.application_source == 'email'])

                bot_username = (await query.bot.me()).username
                deep_link = f"https://t.me/{bot_username}?start=job_{vacancy.id}"

                status_text = "✅ Активна" if vacancy.is_active else "❌ Неактивна"

                text = f"""
📋 <b>{vacancy.title}</b>

📊 <b>Статус:</b> {status_text}
🆔 <b>ID:</b> {vacancy.id}
📅 <b>Создана:</b> {vacancy.created_at.strftime('%d.%m.%Y %H:%M')}

📝 <b>Описание:</b>
{vacancy.description if vacancy.description else 'Не указано'}

✅ <b>Требования:</b>
{vacancy.requirements if vacancy.requirements else 'Не указаны'}

📊 <b>Статистика откликов:</b>
• Всего: {len(applications)}
• Через Telegram: {telegram_apps} 📱
• Через Email: {email_apps} 📧

🔗 <b>Deep link:</b>
<code>{deep_link}</code>
"""

                from urllib.parse import quote
                desc_text = f"\n\n📝 {vacancy.description}" if vacancy.description else ""
                share_text = f"🔥 Вакансия: {vacancy.title}{desc_text}"
                share_url = f"https://t.me/share/url?url={quote(deep_link)}&text={quote(share_text)}"

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Активировать" if not vacancy.is_active else "❌ Деактивировать",
                            callback_data=VacancyManageCallback(
                                vacancy_id=vacancy.id,
                                action="deactivate" if vacancy.is_active else "activate"
                            ).pack()
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="📊 Посмотреть отклики",
                            callback_data=f"vacancy:{vacancy.id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(text="📤 Поделиться вакансией", url=share_url)
                    ],
                    [
                        InlineKeyboardButton(text="◀ Назад к списку", callback_data="back_to_vacancies_list")
                    ]
                ])

                await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

            elif callback_data.action == "activate":
                vacancy.is_active = True
                await session.commit()

                await query.message.answer(f"✅ Вакансия «{vacancy.title}» активирована!")

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀ Назад", callback_data=VacancyManageCallback(vacancy_id=vacancy.id, action="view").pack())]
                ])
                await query.message.edit_reply_markup(reply_markup=keyboard)

            elif callback_data.action == "deactivate":
                vacancy.is_active = False
                await session.commit()

                await query.message.answer(f"❌ Вакансия «{vacancy.title}» деактивирована. Новые отклики больше не принимаются.")

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀ Назад", callback_data=VacancyManageCallback(vacancy_id=vacancy.id, action="view").pack())]
                ])
                await query.message.edit_reply_markup(reply_markup=keyboard)

    @dp.callback_query(F.data == "back_to_vacancies_list")
    async def back_to_vacancies(query: CallbackQuery, user: TelegramUser):
        await query.answer()

        async with AsyncSessionLocal() as session:
            stmt = select(Vacancy).order_by(desc(Vacancy.created_at))
            result = await session.execute(stmt)
            vacancies = result.scalars().all()

            text = "📋 <b>Все вакансии:</b>\n\n"

            keyboard_buttons = []
            for vacancy in vacancies:
                status_icon = "✅" if vacancy.is_active else "❌"

                stmt_apps = select(Application).where(Application.vacancy_id == vacancy.id)
                apps_result = await session.execute(stmt_apps)
                apps_count = len(apps_result.scalars().all())

                text += f"{status_icon} <b>{vacancy.title}</b>\n"
                text += f"   📊 Откликов: {apps_count}\n"
                text += f"   📅 Создана: {vacancy.created_at.strftime('%d.%m.%Y')}\n\n"

                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"⚙️ {vacancy.title}",
                        callback_data=VacancyManageCallback(vacancy_id=vacancy.id, action="view").pack()
                    )
                ])

            keyboard_buttons.append([
                InlineKeyboardButton(text="➕ Создать вакансию", callback_data="create_new_vacancy")
            ])

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
