"""Middleware для проверки прав доступа"""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from shared.database.database import AsyncSessionLocal
from shared.models.user import TelegramUser, RoleEnum


class RoleCheckMiddleware(BaseMiddleware):
    """Middleware для проверки ролей пользователей"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем telegram_id пользователя
        if isinstance(event, Message):
            telegram_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
        elif isinstance(event, CallbackQuery):
            telegram_id = event.from_user.id
            username = event.from_user.username
            first_name = event.from_user.first_name
            last_name = event.from_user.last_name
        else:
            return await handler(event, data)

        # Получаем или создаем пользователя в БД
        async with AsyncSessionLocal() as session:
            stmt = select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                # Создаем нового пользователя с ролью USER
                user = TelegramUser(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    role=RoleEnum.USER
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

            # Добавляем пользователя в data для использования в хендлерах
            data['user'] = user

        return await handler(event, data)


def has_permission(permission: str):
    """
    Декоратор для проверки прав доступа

    Usage:
        @dp.message(Command("parse"))
        @has_permission('parse_emails')
        async def parse_handler(message: Message, user: TelegramUser):
            ...
    """
    def decorator(handler):
        async def wrapper(event: Message | CallbackQuery, *args, user: TelegramUser = None, **kwargs):
            if not user:
                if isinstance(event, Message):
                    await event.answer("❌ Ошибка авторизации")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ Ошибка авторизации", show_alert=True)
                return

            if not user.has_permission(permission):
                if isinstance(event, Message):
                    await event.answer("❌ У вас нет прав для выполнения этой команды")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ У вас нет прав для выполнения этого действия", show_alert=True)
                return

            return await handler(event, *args, user=user, **kwargs)

        return wrapper
    return decorator


def admin_only(handler):
    """
    Декоратор для проверки прав администратора

    Usage:
        @dp.message(Command("accounts"))
        @admin_only
        async def accounts_handler(message: Message, user: TelegramUser):
            ...
    """
    async def wrapper(event: Message | CallbackQuery, *args, user: TelegramUser = None, **kwargs):
        if not user or not user.is_admin:
            if isinstance(event, Message):
                await event.answer("❌ Эта команда доступна только администраторам")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Это действие доступно только администраторам", show_alert=True)
            return

        return await handler(event, *args, user=user, **kwargs)

    return wrapper


def moderator_or_admin(handler):
    """
    Декоратор для проверки прав модератора или администратора

    Usage:
        @dp.message(Command("recent"))
        @moderator_or_admin
        async def recent_handler(message: Message, user: TelegramUser):
            ...
    """
    async def wrapper(event: Message | CallbackQuery, *args, user: TelegramUser = None, **kwargs):
        if not user or (not user.is_moderator and not user.is_admin):
            if isinstance(event, Message):
                await event.answer("❌ Эта команда доступна только модераторам и администраторам")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Это действие доступно только модераторам и администраторам", show_alert=True)
            return

        return await handler(event, *args, user=user, **kwargs)

    return wrapper
