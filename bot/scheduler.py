import asyncio
import logging
import json
import os
from datetime import datetime
from bot.gmail_parser import GmailParser

logger = logging.getLogger(__name__)

class GmailScheduler:
    def __init__(self, interval_minutes: int = 5, accounts_config_path: str = "bot/gmail_accounts.json"):
        """
        Планировщик для периодической проверки Gmail

        Args:
            interval_minutes: Интервал проверки в минутах (по умолчанию 5 минут)
            accounts_config_path: Путь к файлу конфигурации аккаунтов
        """
        self.interval_minutes = interval_minutes
        self.accounts_config_path = accounts_config_path
        self.parsers = []
        self.is_running = False
        self.task = None
        self._load_accounts()

    def _load_accounts(self):
        """Загружает конфигурацию аккаунтов и создает парсеры"""
        try:
            if not os.path.exists(self.accounts_config_path):
                logger.warning(f"Файл конфигурации {self.accounts_config_path} не найден. Используется дефолтный аккаунт.")
                self.parsers = [GmailParser()]
                return

            with open(self.accounts_config_path, 'r', encoding='utf-8') as f:
                accounts = json.load(f)

            for account in accounts:
                if account.get('enabled', True):
                    parser = GmailParser(
                        account_id=account['id'],
                        credentials_path=account['credentials_path'],
                        token_path=account['token_path']
                    )
                    self.parsers.append(parser)
                    logger.info(f"📧 Добавлен аккаунт: {account.get('name', account['id'])}")

            if not self.parsers:
                logger.warning("Нет активных аккаунтов. Используется дефолтный аккаунт.")
                self.parsers = [GmailParser()]

        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации аккаунтов: {e}")
            logger.info("Используется дефолтный аккаунт")
            self.parsers = [GmailParser()]

    async def check_emails(self):
        """Проверяет новые письма и парсит их из всех аккаунтов"""
        try:
            logger.info(f"[{datetime.now().strftime('%H:%M:%S')}] Запуск автоматической проверки Gmail...")

            total_parsed = 0
            all_new_vacancies = []

            # Проверяем все аккаунты
            for parser in self.parsers:
                try:
                    result = await parser.parse_new_emails()

                    if result['parsed_count'] > 0:
                        total_parsed += result['parsed_count']
                        logger.info(f"✅ [{parser.account_id}] Обработано откликов: {result['parsed_count']}")

                        if result['new_vacancies']:
                            all_new_vacancies.extend(result['new_vacancies'])
                            logger.info(f"📋 [{parser.account_id}] Новые вакансии: {', '.join(result['new_vacancies'])}")
                    else:
                        logger.info(f"📭 [{parser.account_id}] Новых откликов не найдено")

                except Exception as e:
                    logger.error(f"❌ Ошибка при проверке аккаунта {parser.account_id}: {e}")

            # Итоговая статистика
            if total_parsed > 0:
                logger.info(f"📊 Всего обработано откликов: {total_parsed}")
                if all_new_vacancies:
                    unique_vacancies = list(set(all_new_vacancies))
                    logger.info(f"📋 Всего новых вакансий: {len(unique_vacancies)}")

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
