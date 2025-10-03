import asyncio
import logging
from datetime import datetime
from bot.gmail_parser import GmailParser

logger = logging.getLogger(__name__)

class GmailScheduler:
    def __init__(self, interval_minutes: int = 5):
        """
        Планировщик для периодической проверки Gmail

        Args:
            interval_minutes: Интервал проверки в минутах (по умолчанию 5 минут)
        """
        self.interval_minutes = interval_minutes
        self.parser = GmailParser()
        self.is_running = False
        self.task = None

    async def check_emails(self):
        """Проверяет новые письма и парсит их"""
        try:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Запуск автоматической проверки Gmail...")
            result = await self.parser.parse_new_emails()

            if result['parsed_count'] > 0:
                logger.info(f"✅ Обработано откликов: {result['parsed_count']}")
                if result['new_vacancies']:
                    logger.info(f"📋 Новые вакансии: {', '.join(result['new_vacancies'])}")
            else:
                logger.info("📭 Новых откликов не найдено")

        except Exception as e:
            logger.error(f"❌ Ошибка при проверке Gmail: {e}")

    async def start(self):
        """Запускает периодическую проверку"""
        if self.is_running:
            logger.warning("Scheduler уже запущен")
            return

        self.is_running = True
        logger.info(f"🚀 Scheduler запущен. Интервал проверки: {self.interval_minutes} мин.")

        while self.is_running:
            await self.check_emails()
            await asyncio.sleep(self.interval_minutes * 60)

    async def start_background(self):
        """Запускает scheduler в фоновом режиме"""
        if self.task and not self.task.done():
            logger.warning("Scheduler уже запущен в фоне")
            return

        self.task = asyncio.create_task(self.start())
        logger.info(f"🔄 Scheduler запущен в фоне (интервал: {self.interval_minutes} мин.)")

    async def stop(self):
        """Останавливает проверку"""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("⏹️ Scheduler остановлен")
