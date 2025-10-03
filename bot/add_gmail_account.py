#!/usr/bin/env python3
"""
Скрипт для добавления нового Gmail аккаунта в бота
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


def get_gmail_email(service):
    """Получает email адрес аутентифицированного пользователя"""
    try:
        profile = service.users().getProfile(userId='me').execute()
        return profile.get('emailAddress')
    except Exception as e:
        print(f"Ошибка получения email: {e}")
        return None


def authenticate_new_account():
    """Авторизует новый Gmail аккаунт и возвращает credentials и email"""
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"❌ Файл {CREDENTIALS_PATH} не найден!")
        print(f"Создайте OAuth приложение в Google Cloud Console и сохраните credentials.json")
        return None, None

    print("🔐 Начинаем авторизацию нового Gmail аккаунта...")
    print("Откроется браузер, выберите нужный Gmail аккаунт")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    # Получаем email адрес
    service = build('gmail', 'v1', credentials=creds)
    email = get_gmail_email(service)

    return creds, email


def load_accounts_config():
    """Загружает конфигурацию аккаунтов"""
    if not os.path.exists(ACCOUNTS_CONFIG_PATH):
        return []

    with open(ACCOUNTS_CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_accounts_config(accounts):
    """Сохраняет конфигурацию аккаунтов"""
    os.makedirs(os.path.dirname(ACCOUNTS_CONFIG_PATH), exist_ok=True)
    with open(ACCOUNTS_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(accounts, f, indent=2, ensure_ascii=False)


def generate_account_id(email):
    """Генерирует ID аккаунта из email"""
    # Берем часть до @ и очищаем от точек
    username = email.split('@')[0].replace('.', '_')
    return username


def add_account_to_config(account_id, account_name, token_path):
    """Добавляет новый аккаунт в конфигурацию"""
    accounts = load_accounts_config()

    # Проверяем, не существует ли уже такой аккаунт
    for account in accounts:
        if account['id'] == account_id:
            print(f"⚠️  Аккаунт с ID '{account_id}' уже существует")
            return False

    new_account = {
        "id": account_id,
        "name": account_name,
        "credentials_path": "gmail_tokens/credentials.json",
        "token_path": token_path,
        "enabled": False  # По умолчанию отключен
    }

    accounts.append(new_account)
    save_accounts_config(accounts)

    return True


def main():
    print("=" * 60)
    print("📧 Добавление нового Gmail аккаунта в HR бота")
    print("=" * 60)
    print()

    # Создаем папку для токенов если её нет
    os.makedirs('gmail_tokens', exist_ok=True)

    # Авторизуем новый аккаунт
    creds, email = authenticate_new_account()

    if not creds or not email:
        print("❌ Авторизация не удалась")
        return

    print()
    print(f"✅ Успешная авторизация!")
    print(f"📧 Email: {email}")
    print()

    # Генерируем ID и путь к токену
    suggested_id = generate_account_id(email)

    # Спрашиваем пользователя о деталях
    print(f"ID аккаунта (предложенный: {suggested_id}): ", end='')
    account_id = input().strip() or suggested_id

    print(f"Название аккаунта (предложенное: {email}): ", end='')
    account_name = input().strip() or email

    # Путь к токену
    token_path = f"gmail_tokens/token_{account_id}.json"

    # Сохраняем токен
    print()
    print(f"💾 Сохраняем токен в {token_path}...")
    with open(token_path, 'w') as token_file:
        token_file.write(creds.to_json())

    # Добавляем в конфигурацию
    print(f"📝 Добавляем аккаунт в конфигурацию...")
    if add_account_to_config(account_id, account_name, token_path):
        print()
        print("=" * 60)
        print("✅ ГОТОВО! Новый аккаунт успешно добавлен")
        print("=" * 60)
        print()
        print(f"ID аккаунта: {account_id}")
        print(f"Название: {account_name}")
        print(f"Email: {email}")
        print(f"Токен: {token_path}")
        print(f"Статус: ⚠️  ОТКЛЮЧЕН (по умолчанию)")
        print()
        print("📱 Чтобы включить аккаунт, используйте команду /accounts в боте")
    else:
        print("❌ Не удалось добавить аккаунт в конфигурацию")


if __name__ == '__main__':
    main()
