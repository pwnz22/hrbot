import os
import re
import aiofiles
import base64
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy.exc import IntegrityError
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Vacancy

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailParser:
    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def extract_contact_info(self, text):
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+?[7-8][\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2})'

        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)

        return {
            'email': emails[0] if emails else None,
            'phone': phones[0] if phones else None
        }

    async def download_attachment(self, message_id, attachment_id, filename):
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id
            ).execute()

            file_data = base64.urlsafe_b64decode(attachment['data'])
            file_path = f"downloads/{message_id}_{filename}"

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)

            return file_path
        except Exception as e:
            print(f"Ошибка загрузки вложения: {e}")
            return None

    async def parse_new_emails(self):
        try:
            results = self.service.users().messages().list(
                userId='me', q='is:unread'
            ).execute()

            messages = results.get('messages', [])

            for message in messages:
                await self.process_message(message['id'])

        except Exception as e:
            print(f"Ошибка парсинга писем: {e}")

    async def process_message(self, message_id):
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()

            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')

            body = self.extract_body(message['payload'])
            contact_info = self.extract_contact_info(f"{subject} {body} {from_email}")

            file_path = None
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part.get('filename'):
                        file_path = await self.download_attachment(
                            message_id, part['body']['attachmentId'], part['filename']
                        )
                        break

            name = self.extract_name(from_email, body)

            async with AsyncSessionLocal() as session:
                vacancy = Vacancy(
                    name=name,
                    email=contact_info['email'] or from_email,
                    phone=contact_info['phone'],
                    file_path=file_path,
                    gmail_message_id=message_id,
                    email_subject=subject,
                    email_body=body[:1000]
                )

                session.add(vacancy)
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()

        except Exception as e:
            print(f"Ошибка обработки сообщения {message_id}: {e}")

    def extract_body(self, payload):
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        else:
            if payload['mimeType'] == 'text/plain':
                data = payload['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        return body

    def extract_name(self, from_email, body):
        name_match = re.search(r'([А-Яа-я]+\s+[А-Яа-я]+)', body)
        if name_match:
            return name_match.group(1)

        email_name = re.search(r'(.+?)\s*<', from_email)
        if email_name:
            return email_name.group(1).strip()

        return from_email.split('@')[0]