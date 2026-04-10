"""FSM-флоу приёма отклика от кандидата через бота (Task 5)."""
import os
import re
from datetime import datetime

from aiogram import Dispatcher, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.filters.callback_data import CallbackData
from sqlalchemy import select

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Vacancy, Application
from shared.models.user import TelegramUser, RoleEnum


BOT_RESUME_DIR = "downloads/bot"
ALLOWED_RESUME_EXT = {".pdf", ".docx", ".doc"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ApplyStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_email = State()
    waiting_message = State()
    waiting_resume = State()
    waiting_confirm = State()


class ApplyCallback(CallbackData, prefix="apply"):
    action: str  # "start", "skip", "confirm", "cancel"
    vacancy_id: int = 0


def _skip_kb(action_name: str = "skip") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="⏭ Пропустить",
                callback_data=ApplyCallback(action=action_name).pack(),
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=ApplyCallback(action="cancel").pack(),
            ),
        ]]
    )


def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Отправить",
                callback_data=ApplyCallback(action="confirm").pack(),
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=ApplyCallback(action="cancel").pack(),
            ),
        ]]
    )


def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=ApplyCallback(action="cancel").pack(),
            ),
        ]]
    )


async def _get_open_vacancy(vacancy_id: int) -> Vacancy | None:
    async with AsyncSessionLocal() as session:
        stmt = select(Vacancy).where(
            Vacancy.id == vacancy_id,
            Vacancy.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def show_open_vacancies_list(message: Message) -> None:
    """Показывает обычному пользователю список открытых вакансий (inline-кнопки)."""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Vacancy)
            .where(Vacancy.deleted_at.is_(None))
            .order_by(Vacancy.created_at.desc())
        )
        result = await session.execute(stmt)
        vacancies = result.scalars().all()

    if not vacancies:
        await message.answer(
            "Сейчас нет открытых вакансий. Загляните позже.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    rows = [
        [InlineKeyboardButton(
            text=f"📢 {v.title}",
            callback_data=ApplyCallback(action="view", vacancy_id=v.id).pack(),
        )]
        for v in vacancies
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer(
        "<b>Открытые вакансии</b>\n\nВыберите вакансию, чтобы откликнуться:",
        reply_markup=kb,
        parse_mode="HTML",
    )


async def show_vacancy_and_offer_apply(message: Message, vacancy_id: int) -> None:
    """Показывает карточку вакансии и кнопку 'Откликнуться'."""
    vacancy = await _get_open_vacancy(vacancy_id)
    if not vacancy:
        await message.answer("❌ Вакансия не найдена или больше не активна.")
        return

    text = f"<b>📢 {vacancy.title}</b>\n\n"
    if vacancy.description:
        text += f"{vacancy.description}\n\n"
    text += "Чтобы откликнуться, нажмите кнопку ниже."

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="📨 Откликнуться",
                callback_data=ApplyCallback(action="start", vacancy_id=vacancy.id).pack(),
            )
        ]]
    )
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


def setup_apply_handlers(dp: Dispatcher) -> None:
    """Регистрирует FSM-хендлеры приёма отклика."""

    @dp.callback_query(ApplyCallback.filter(F.action == "view"))
    async def apply_view(
        callback: CallbackQuery,
        callback_data: ApplyCallback,
    ):
        await show_vacancy_and_offer_apply(callback.message, callback_data.vacancy_id)
        await callback.answer()

    @dp.callback_query(ApplyCallback.filter(F.action == "start"))
    async def apply_start(
        callback: CallbackQuery,
        callback_data: ApplyCallback,
        state: FSMContext,
        user: TelegramUser,
    ):
        vacancy = await _get_open_vacancy(callback_data.vacancy_id)
        if not vacancy:
            await callback.answer("Вакансия недоступна", show_alert=True)
            return

        await state.clear()
        await state.set_state(ApplyStates.waiting_name)
        await state.update_data(vacancy_id=vacancy.id, vacancy_title=vacancy.title)
        await callback.message.answer(
            f"✍️ Отклик на вакансию: <b>{vacancy.title}</b>\n\n"
            "Шаг 1/5. Введите ваше <b>ФИО</b>:",
            reply_markup=_cancel_kb(),
            parse_mode="HTML",
        )
        await callback.answer()

    @dp.message(Command("cancel"), F.chat.type == "private")
    async def cancel_cmd(message: Message, state: FSMContext):
        current = await state.get_state()
        if current and current.startswith("ApplyStates"):
            await state.clear()
            await message.answer("❌ Отклик отменён.", reply_markup=ReplyKeyboardRemove())

    @dp.callback_query(ApplyCallback.filter(F.action == "cancel"))
    async def apply_cancel(callback: CallbackQuery, state: FSMContext):
        await state.clear()
        await callback.message.answer("❌ Отклик отменён.")
        await callback.answer()

    @dp.message(ApplyStates.waiting_name, F.text)
    async def apply_name(message: Message, state: FSMContext):
        name = (message.text or "").strip()
        if len(name) < 2 or len(name) > 150:
            await message.answer(
                "Имя слишком короткое или длинное. Введите ФИО (2–150 символов):",
                reply_markup=_cancel_kb(),
            )
            return
        await state.update_data(name=name)
        await state.set_state(ApplyStates.waiting_phone)
        await message.answer(
            "Шаг 2/5. 📱 Введите ваш <b>телефон</b> (например, +992900000000):",
            reply_markup=_cancel_kb(),
            parse_mode="HTML",
        )

    @dp.message(ApplyStates.waiting_phone, F.text)
    async def apply_phone(message: Message, state: FSMContext):
        raw = (message.text or "").strip()
        digits = re.sub(r"[^\d+]", "", raw)
        if len(re.sub(r"\D", "", digits)) < 7:
            await message.answer(
                "Телефон некорректен. Введите ещё раз (минимум 7 цифр):",
                reply_markup=_cancel_kb(),
            )
            return
        await state.update_data(phone=digits)
        await state.set_state(ApplyStates.waiting_email)
        await message.answer(
            "Шаг 3/5. 📧 Введите ваш <b>email</b>:",
            reply_markup=_cancel_kb(),
            parse_mode="HTML",
        )

    @dp.message(ApplyStates.waiting_email, F.text)
    async def apply_email(message: Message, state: FSMContext):
        email = (message.text or "").strip().lower()
        if not EMAIL_RE.match(email):
            await message.answer(
                "Email некорректен. Введите ещё раз:",
                reply_markup=_cancel_kb(),
            )
            return
        await state.update_data(email=email)
        await state.set_state(ApplyStates.waiting_message)
        await message.answer(
            "Шаг 4/5. 📝 Напишите сопроводительное сообщение (или нажмите «Пропустить»):",
            reply_markup=_skip_kb("skip"),
        )

    @dp.message(ApplyStates.waiting_message, F.text)
    async def apply_message_text(message: Message, state: FSMContext):
        text = (message.text or "").strip()
        if len(text) > 4000:
            text = text[:4000]
        await state.update_data(applicant_message=text)
        await _goto_resume_step(message, state)

    @dp.callback_query(ApplyStates.waiting_message, ApplyCallback.filter(F.action == "skip"))
    async def apply_message_skip(callback: CallbackQuery, state: FSMContext):
        await state.update_data(applicant_message=None)
        await _goto_resume_step(callback.message, state)
        await callback.answer()

    async def _goto_resume_step(message: Message, state: FSMContext):
        await state.set_state(ApplyStates.waiting_resume)
        await message.answer(
            "Шаг 5/5. 📎 Прикрепите резюме (PDF/DOCX) или нажмите «Пропустить»:",
            reply_markup=_skip_kb("skip"),
        )

    @dp.message(ApplyStates.waiting_resume, F.document)
    async def apply_resume_doc(message: Message, state: FSMContext, bot: Bot):
        doc = message.document
        filename = doc.file_name or f"resume_{doc.file_unique_id}"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_RESUME_EXT:
            await message.answer(
                f"Формат не поддерживается. Разрешены: {', '.join(sorted(ALLOWED_RESUME_EXT))}.\n"
                "Пришлите другой файл или нажмите «Пропустить».",
                reply_markup=_skip_kb("skip"),
            )
            return
        if doc.file_size and doc.file_size > 20 * 1024 * 1024:
            await message.answer("Файл слишком большой (>20 МБ). Пришлите другой.")
            return

        data = await state.get_data()
        vacancy_id = data.get("vacancy_id", 0)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r"[^\w.\-]+", "_", filename)
        target_dir = os.path.join(BOT_RESUME_DIR, str(vacancy_id))
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, f"{ts}_{safe_name}")

        try:
            file = await bot.get_file(doc.file_id)
            await bot.download_file(file.file_path, destination=target_path)
        except Exception as e:
            await message.answer(f"Не удалось сохранить файл: {e}. Попробуйте ещё раз или пропустите.")
            return

        await state.update_data(file_path=target_path, attachment_filename=filename)
        await _goto_confirm_step(message, state)

    @dp.message(ApplyStates.waiting_resume, F.text)
    async def apply_resume_wrong(message: Message, state: FSMContext):
        await message.answer(
            "Пришлите файл резюме (PDF/DOCX) как документ или нажмите «Пропустить».",
            reply_markup=_skip_kb("skip"),
        )

    @dp.callback_query(ApplyStates.waiting_resume, ApplyCallback.filter(F.action == "skip"))
    async def apply_resume_skip(callback: CallbackQuery, state: FSMContext):
        await state.update_data(file_path=None, attachment_filename=None)
        await _goto_confirm_step(callback.message, state)
        await callback.answer()

    async def _goto_confirm_step(message: Message, state: FSMContext):
        data = await state.get_data()
        await state.set_state(ApplyStates.waiting_confirm)
        summary = (
            "<b>Проверьте отклик:</b>\n\n"
            f"📢 Вакансия: <b>{data.get('vacancy_title', '—')}</b>\n"
            f"👤 ФИО: {data.get('name', '—')}\n"
            f"📱 Телефон: {data.get('phone', '—')}\n"
            f"📧 Email: {data.get('email', '—')}\n"
        )
        msg = data.get("applicant_message")
        if msg:
            summary += f"📝 Сообщение: {msg}\n"
        if data.get("attachment_filename"):
            summary += f"📎 Резюме: {data['attachment_filename']}\n"
        summary += "\nОтправить отклик?"
        await message.answer(summary, reply_markup=_confirm_kb(), parse_mode="HTML")

    @dp.callback_query(ApplyStates.waiting_confirm, ApplyCallback.filter(F.action == "confirm"))
    async def apply_confirm(callback: CallbackQuery, state: FSMContext, user: TelegramUser, bot: Bot):
        data = await state.get_data()
        vacancy_id = data.get("vacancy_id")
        vacancy = await _get_open_vacancy(vacancy_id) if vacancy_id else None
        if not vacancy:
            await state.clear()
            await callback.message.answer("❌ Вакансия больше недоступна, отклик не отправлен.")
            await callback.answer()
            return

        async with AsyncSessionLocal() as session:
            app = Application(
                name=data.get("name", ""),
                email=data.get("email"),
                phone=data.get("phone"),
                file_path=data.get("file_path"),
                attachment_filename=data.get("attachment_filename"),
                gmail_message_id=None,
                applicant_message=data.get("applicant_message"),
                vacancy_id=vacancy.id,
                is_processed=False,
                source="bot",
                telegram_user_id=user.telegram_id if user else None,
            )
            session.add(app)
            await session.commit()
            await session.refresh(app)
            application_id = app.id

        await state.clear()
        await callback.message.answer(
            "✅ Отклик отправлен! HR-команда свяжется с вами."
        )
        await callback.answer("Готово")

        try:
            await _notify_staff(bot, vacancy, data, application_id)
        except Exception:
            pass

    async def _notify_staff(bot: Bot, vacancy: Vacancy, data: dict, application_id: int):
        async with AsyncSessionLocal() as session:
            stmt = select(TelegramUser).where(
                TelegramUser.role.in_([RoleEnum.MODERATOR, RoleEnum.ADMIN])
            )
            result = await session.execute(stmt)
            staff = result.scalars().all()

        text = (
            "🆕 <b>Новый отклик через бота</b>\n\n"
            f"📢 Вакансия: <b>{vacancy.title}</b>\n"
            f"👤 {data.get('name', '—')}\n"
            f"📱 {data.get('phone', '—')}\n"
            f"📧 {data.get('email', '—')}\n"
        )
        if data.get("applicant_message"):
            text += f"📝 {data['applicant_message'][:300]}\n"
        if data.get("attachment_filename"):
            text += f"📎 {data['attachment_filename']}\n"
        text += f"\nID отклика: <code>{application_id}</code>"

        for member in staff:
            try:
                await bot.send_message(member.telegram_id, text, parse_mode="HTML")
            except Exception:
                continue
