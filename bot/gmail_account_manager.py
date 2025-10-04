"""
Менеджер для управления Gmail аккаунтами
"""
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_PATH = 'gmail_tokens/credentials.json'
ACCOUNTS_CONFIG_PATH = 'bot/gmail_accounts.json'


class GmailAccountManager:
    """Управление Gmail аккаунтами для бота"""

    @staticmethod
    def load_accounts():
        """Загружает список аккаунтов"""
        if not os.path.exists(ACCOUNTS_CONFIG_PATH):
            return []

        with open(ACCOUNTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def save_accounts(accounts):
        """Сохраняет список аккаунтов"""
        os.makedirs(os.path.dirname(ACCOUNTS_CONFIG_PATH), exist_ok=True)
        with open(ACCOUNTS_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(accounts, f, indent=2, ensure_ascii=False)

    @staticmethod
    def generate_auth_url():
        """
        Генерирует OAuth URL для авторизации
        Возвращает: (success: bool, auth_url: str или error_message: str, flow_data: dict или None)
        """
        # Проверяем наличие credentials
        if not os.path.exists(CREDENTIALS_PATH):
            return False, "❌ Файл credentials.json не найден в gmail_tokens/", None

        try:
            # Создаем OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # Для manual copy/paste
            )

            auth_url, _ = flow.authorization_url(prompt='consent')

            # Сохраняем flow данные для последующего использования
            flow_data = {
                'client_config': flow.client_config,
                'scopes': SCOPES
            }

            return True, auth_url, flow_data

        except Exception as e:
            return False, f"❌ Ошибка генерации URL: {str(e)}", None

    @staticmethod
    def complete_auth_with_code(auth_code):
        """
        Завершает авторизацию используя код от пользователя
        Возвращает: (success: bool, message: str, account_data: dict или None)
        """
        # Проверяем наличие credentials
        if not os.path.exists(CREDENTIALS_PATH):
            return False, "❌ Файл credentials.json не найден в gmail_tokens/", None

        try:
            # Создаем flow заново
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )

            # Получаем токен используя код
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            # Получаем email адрес
            service = build('gmail', 'v1', credentials=creds)
            profile = service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress')

            if not email:
                return False, "❌ Не удалось получить email адрес", None

            # Генерируем ID
            account_id = email.split('@')[0].replace('.', '_')

            # Загружаем существующие аккаунты
            accounts = GmailAccountManager.load_accounts()

            # Проверяем дубликаты
            for account in accounts:
                if account['id'] == account_id:
                    return False, f"⚠️ Аккаунт {email} уже добавлен", None

            # Сохраняем token
            token_path = f"gmail_tokens/token_{account_id}.json"
            os.makedirs('gmail_tokens', exist_ok=True)

            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())

            # Создаем запись аккаунта
            new_account = {
                "id": account_id,
                "name": email,
                "credentials_path": CREDENTIALS_PATH,
                "token_path": token_path,
                "enabled": False  # По умолчанию отключен
            }

            # Добавляем в список
            accounts.append(new_account)
            GmailAccountManager.save_accounts(accounts)

            success_message = (
                f"✅ Аккаунт успешно добавлен!\n"
                f"📧 Email: {email}\n"
                f"🆔 ID: {account_id}\n"
                f"🏷️ Статус: ❌ Отключен (по умолчанию)"
            )

            return True, success_message, new_account

        except Exception as e:
            return False, f"❌ Ошибка авторизации: {str(e)}", None

    @staticmethod
    def toggle_account(account_id, enable):
        """
        Включает или отключает аккаунт
        Возвращает: (success: bool, message: str)
        """
        accounts = GmailAccountManager.load_accounts()

        for account in accounts:
            if account['id'] == account_id:
                account['enabled'] = enable
                GmailAccountManager.save_accounts(accounts)

                status = "включен" if enable else "отключен"
                return True, f"✅ Аккаунт {account.get('name', account_id)} {status}"

        return False, "❌ Аккаунт не найден"

    @staticmethod
    def get_account(account_id):
        """Возвращает данные конкретного аккаунта"""
        accounts = GmailAccountManager.load_accounts()

        for account in accounts:
            if account['id'] == account_id:
                return account

        return None

    @staticmethod
    def remove_account(account_id):
        """
        Удаляет аккаунт из конфигурации и удаляет token файл
        Возвращает: (success: bool, message: str)
        """
        accounts = GmailAccountManager.load_accounts()

        account_to_remove = None
        for i, account in enumerate(accounts):
            if account['id'] == account_id:
                account_to_remove = account
                accounts.pop(i)
                break

        if not account_to_remove:
            return False, "❌ Аккаунт не найден"

        # Удаляем token файл
        token_path = account_to_remove.get('token_path')
        if token_path and os.path.exists(token_path):
            try:
                os.remove(token_path)
            except Exception as e:
                print(f"Не удалось удалить token файл: {e}")

        # Сохраняем обновленный список
        GmailAccountManager.save_accounts(accounts)

        return True, f"✅ Аккаунт {account_to_remove.get('name', account_id)} удален"
