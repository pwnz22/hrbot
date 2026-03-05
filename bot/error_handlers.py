import logging
from aiogram import Dispatcher
from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)

async def error_handler(event: ErrorEvent):
    logger.error(f"Update {event.update.update_id} caused error: {event.exception}", exc_info=True)

    try:
        if event.update.message:
            await event.update.message.answer(f"❌ Произошла ошибка: {str(event.exception)}")
        elif event.update.callback_query:
            await event.update.callback_query.message.answer(f"❌ Произошла ошибка: {str(event.exception)}")
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")

    return True

def setup_error_handlers(dp: Dispatcher):
    dp.error.register(error_handler)
