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
from bs4 import BeautifulSoup
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.database.database import AsyncSessionLocal
from shared.models.vacancy import Application, Vacancy
from shared.services.resume_summary_service import ResumeSummaryService

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailParser:
    def __init__(self, account_id="main", credentials_path="gmail_tokens/credentials.json", token_path="gmail_tokens/token_main.json"):
        self.account_id = account_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.resume_summary_service = ResumeSummaryService()
        self.authenticate()

    def authenticate(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)
        print(f"✅ Аутентификация выполнена для аккаунта: {self.account_id}")

    def extract_contact_info(self, text):
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+?[7-8][\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2})'

        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)

        return {
            'email': emails[0] if emails else None,
            'phone': phones[0] if phones else None
        }

    async def download_attachment(self, message_id, attachment_id, filename, applicant_name="Unknown"):
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me', messageId=message_id, id=attachment_id
            ).execute()

            file_data = base64.urlsafe_b64decode(attachment['data'])

            # Очищаем имя от недопустимых символов для имени файла
            safe_name = "".join(c for c in applicant_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')

            file_path = f"downloads/{safe_name}_{filename}"

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)

            return file_path
        except Exception as e:
            print(f"Ошибка загрузки вложения: {e}")
            return None

    async def parse_new_emails(self):
        parsed_count = 0
        new_vacancies = []

        try:
            print(f"📧 Проверка аккаунта: {self.account_id}")
            # Фильтруем письма от SomonTj с нужным заголовком (включая прочитанные)
            query = 'from:noreply@somon.tj subject:"Отклик на вакансию"'
            results = self.service.users().messages().list(
                userId='me', q=query
            ).execute()

            messages = results.get('messages', [])

            for message in messages:
                result = await self.process_message(message['id'])
                if result and result.get('success'):
                    parsed_count += 1

                    # Добавляем новую вакансию в список если она была создана
                    if result.get('new_vacancy'):
                        vacancy_title = result.get('vacancy_title')
                        if vacancy_title and vacancy_title not in new_vacancies:
                            new_vacancies.append(vacancy_title)

        except Exception as e:
            print(f"Ошибка парсинга писем: {e}")

        return {
            "parsed_count": parsed_count,
            "new_vacancies": new_vacancies
        }

    async def process_message(self, message_id):
        try:
            # Сначала проверяем, не обработано ли уже это письмо или не удалено ли оно
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                existing_check = await session.execute(
                    select(Application).where(Application.gmail_message_id == message_id)
                )
                existing_app = existing_check.scalar_one_or_none()
                if existing_app:
                    if existing_app.deleted_at is not None:
                        print(f"Письмо {message_id} было удалено, пропускаем")
                    else:
                        print(f"Письмо {message_id} уже обработано, пропускаем")
                    return {"success": False}

            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()

            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')

            # Проверяем что письмо от SomonTj
            if 'noreply@somon.tj' not in from_email:
                print(f"Пропускаем письмо не от SomonTj: {from_email}")
                return {"success": False}

            # Проверяем что заголовок начинается с "Отклик на вакансию"
            if not subject.startswith('Отклик на вакансию'):
                print(f"Пропускаем письмо без нужной темы: {subject}")
                return {"success": False}

            print(f"Обрабатываем письмо от SomonTj: {subject}")

            body = self.extract_body(message['payload'])

            contact_info = self.extract_somon_contact_info(body)
            print(f"Извлеченная контактная информация: {contact_info}")

            vacancy_title = self.extract_vacancy_title(subject)
            print(f"Название вакансии: {vacancy_title}")

            # Сохраняем ссылку на вложение вместо скачивания
            attachment_url = None
            attachment_filename = None

            # Ищем ссылки на вложения прямо в HTML
            def find_attachments_in_html(html_body):
                nonlocal attachment_url, attachment_filename
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_body, 'html.parser')

                    # Ищем все ссылки в письме
                    links = soup.find_all('a', href=True)

                    for link in links:
                        href = link['href']
                        link_text = link.get_text().strip()

                        # Ищем ссылки на вложения Gmail с правильным форматом
                        if ('mail.google.com' in href and 'attid=' in href and 'view=att' in href):
                            attachment_url = href
                            # Пробуем извлечь имя файла из текста ссылки или окружающего контекста
                            if link_text and not link_text.startswith('http') and len(link_text) > 3:
                                attachment_filename = link_text
                            print(f"✅ Найдена ссылка на вложение: {attachment_filename}")
                            return True

                        # Альтернативно ищем ссылки на mail-attachment.googleusercontent.com
                        elif 'mail-attachment.googleusercontent.com' in href:
                            attachment_url = href
                            if link_text and not link_text.startswith('http') and len(link_text) > 3:
                                attachment_filename = link_text
                            print(f"✅ Найдена ссылка на вложение: {attachment_filename}")
                            return True

                except Exception as e:
                    print(f"Ошибка поиска ссылок в HTML: {e}")
                return False

            # Сначала ищем готовые ссылки в HTML
            if body:
                find_attachments_in_html(body)

            # Если не нашли в HTML, ищем через parts (старый способ)
            if not attachment_url:
                def find_attachments(parts, depth=0):
                    nonlocal attachment_url, attachment_filename
                    for i, part in enumerate(parts):
                        if part.get('filename') and part.get('filename') != '':
                            attachment_filename = part['filename']
                            attachment_id = part['body'].get('attachmentId')

                            if attachment_id:
                                # Формируем Gmail URL в нужном формате
                                attachment_url = f"https://mail.google.com/mail/u/1?ui=2&ik=21f77b88b6&attid={attachment_id}&permmsgid=msg-f:{message_id}&view=att&zw&disp=inline"
                                print(f"✅ Найдено вложение: {attachment_filename}")
                                return True

                        # Рекурсивно ищем во вложенных parts
                        if 'parts' in part:
                            if find_attachments(part['parts'], depth + 1):
                                return True
                    return False

                if 'parts' in message['payload']:
                    find_attachments(message['payload']['parts'])

            # Сначала извлекаем имя кандидата
            name = contact_info.get('name') or 'Неизвестно'
            if not name or name.strip() == '':
                name = 'Неизвестно'

            # Скачивание файлов с правильным именем
            file_path = None
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part.get('filename'):
                        file_path = await self.download_attachment(
                            message_id, part['body']['attachmentId'], part['filename'], name
                        )
                        break
            email = contact_info.get('email') or ''

            print(f"Подготовка к сохранению: name={name}, email={email}")

            # Находим или создаем вакансию
            async with AsyncSessionLocal() as session:
                vacancy, is_new_vacancy = await self.get_or_create_vacancy(session, vacancy_title)

                application = Application(
                    name=name,
                    email=email,
                    phone=contact_info.get('phone'),
                    file_path=file_path,
                    file_url=attachment_url,
                    attachment_filename=attachment_filename,
                    gmail_message_id=message_id,
                    applicant_message=contact_info.get('message'),
                    vacancy_id=vacancy.id if vacancy else None
                )


                session.add(application)
                try:
                    await session.commit()
                    print(f"✅ УСПЕШНО СОХРАНЕН отклик: {name} - {email} для вакансии: {vacancy_title}")

                    # Generate summary if application has resume file
                    # ВРЕМЕННО ОТКЛЮЧЕНО - генерация через кнопку в боте
                    # try:
                    #     summary = await self.resume_summary_service.generate_summary_for_application(application, vacancy)
                    #     if summary:
                    #         application.summary = summary
                    #         await session.commit()
                    #         print(f"✅ SUMMARY сгенерирован для отклика: {name}")
                    #     else:
                    #         print(f"⚠️ SUMMARY не удалось сгенерировать для отклика: {name}")
                    # except Exception as e:
                    #     print(f"❌ ОШИБКА генерации summary для {name}: {e}")

                    return {
                        "success": True,
                        "new_vacancy": is_new_vacancy,
                        "vacancy_title": vacancy_title
                    }

                except IntegrityError as e:
                    await session.rollback()
                    print(f"❌ Отклик уже существует: {message_id} - {e}")
                    return {"success": False}
                except Exception as e:
                    await session.rollback()
                    print(f"❌ ОШИБКА сохранения: {e}")
                    print(f"Данные: name={name}, email={email}, vacancy_id={vacancy.id if vacancy else None}")
                    return {"success": False}

        except Exception as e:
            print(f"Ошибка обработки сообщения {message_id}: {e}")
            return {"success": False}

    def extract_body(self, payload):
        body = ""

        def extract_from_part(part):
            try:
                if 'data' in part['body'] and part['body']['data']:
                    data = part['body']['data']
                    return base64.urlsafe_b64decode(data).decode('utf-8')
            except Exception as e:
                print(f"Ошибка декодирования части: {e}")
            return ""

        def find_body_recursive(payload_part):
            nonlocal body

            # Если есть данные в этой части
            if payload_part.get('mimeType') in ['text/html', 'text/plain']:
                extracted = extract_from_part(payload_part)
                if extracted and len(extracted) > len(body):
                    body = extracted

            # Рекурсивно ищем в подчастях
            if 'parts' in payload_part:
                for part in payload_part['parts']:
                    find_body_recursive(part)

        # Начинаем поиск
        find_body_recursive(payload)

        # DEBUG сообщения убраны

        return body

    def extract_somon_contact_info(self, html_body):
        """Извлекает контактную информацию из HTML письма SomonTj"""
        try:
            soup = BeautifulSoup(html_body, 'html.parser')
            text = soup.get_text()

            # Очищаем текст от лишних пробелов и переносов
            text = re.sub(r'\s+', ' ', text).strip()

            # print(f"Полный текст письма: {text}")  # Убираем из логов

            # Извлекаем сообщение от кандидата
            applicant_message = None
            message_pattern = r'Текст сообщения:\s*(.*?)(?:Имя:|Email|$)'
            message_match = re.search(message_pattern, text)
            if message_match:
                applicant_message = message_match.group(1).strip()
                # Убираем стандартные фразы
                if 'не предоставил сопроводительного письма' in applicant_message:
                    applicant_message = None

            # Ищем имя (расширенные варианты)
            name = None

            # Сначала пробуем найти через BeautifulSoup более точно
            try:
                # Ищем все <p> теги и проверяем их содержимое
                p_tags = soup.find_all('p')
                for p in p_tags:
                    p_text = p.get_text().strip()
                    if p_text.startswith('Имя:'):
                        name = p_text.replace('Имя:', '').strip()
                        break
            except:
                pass

            # Если не нашли, используем регулярные выражения
            if not name:
                name_patterns = [
                    # Основные варианты (с нормализованными пробелами)
                    r'Имя:\s*(.+?)(?:\s+Email|\s+Телефон|$)',
                    r'Имя\s*[-:]\s*(.+?)(?:\s+Email|\s+Телефон|$)',
                    r'Name:\s*(.+?)(?:\s+Email|\s+Телефон|$)',
                    r'ФИО:\s*(.+?)(?:\s+Email|\s+Телефон|$)',
                    r'Полное имя:\s*(.+?)(?:\s+Email|\s+Телефон|$)',
                    # Варианты с любым текстом между "Текст сообщения:" и "Имя:"
                    r'Текст сообщения:.*?Имя:\s*(.+?)(?:\s+Email|\s+Телефон|$)',
                    # Поиск после "не предоставил сопроводительного письма"
                    r'не предоставил сопроводительного письма.*?Имя:\s*(.+?)(?:\s+Email|\s+Телефон|$)',
                ]

                for pattern in name_patterns:
                    name_match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                    if name_match:
                        candidate_name = name_match.group(1).strip()
                        # Проверяем что это похоже на имя (не слишком длинное и содержит буквы)
                        if len(candidate_name) < 100 and re.search(r'[А-Яа-яA-Za-z]', candidate_name):
                            name = candidate_name
                            break

            # Ищем email
            email = None
            # Ищем ссылки mailto
            email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            if email_links:
                email = email_links[0]['href'].replace('mailto:', '')
            else:
                # Ищем в тексте (расширенные варианты)
                email_patterns = [
                    r'Email для контакта\s*[-:]\s*(.+?)(?:\n|Телефон|$)',
                    r'Email\s*[-:]\s*(.+?)(?:\n|Телефон|$)',
                    r'E-mail\s*[-:]\s*(.+?)(?:\n|Телефон|$)',
                    r'Почта\s*[-:]\s*(.+?)(?:\n|Телефон|$)',
                    r'электронная почта\s*[-:]\s*(.+?)(?:\n|Телефон|$)',
                    # Поиск email адресов в тексте после "не предоставил сопроводительного письма"
                    r'не предоставил сопроводительного письма.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    # Поиск email адресов в тексте
                    r'Текст сообщения:.*?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
                ]

                for pattern in email_patterns:
                    email_match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                    if email_match:
                        candidate_email = email_match.group(1).strip()
                        # Проверяем что это валидный email
                        if '@' in candidate_email and '.' in candidate_email.split('@')[-1]:
                            email = candidate_email
                            break

            # Ищем телефон (расширенные варианты)
            phone = None

            # Сначала пробуем найти через BeautifulSoup
            try:
                p_tags = soup.find_all('p')
                for p in p_tags:
                    p_text = p.get_text().strip()
                    if p_text.startswith('Телефон для контакта'):
                        phone = p_text.replace('Телефон для контакта -', '').replace('Телефон для контакта:', '').strip()
                        break
            except:
                pass

            # Если не нашли, используем регулярные выражения
            if not phone:
                phone_patterns = [
                    r'Телефон для контакта\s*[-:]\s*(.+?)(?:\n|$)',
                    r'Телефон\s*[-:]\s*(.+?)(?:\n|$)',
                    r'Phone\s*[-:]\s*(.+?)(?:\n|$)',
                    r'Моб\.\s*тел\.\s*[-:]\s*(.+?)(?:\n|$)',
                    r'Мобильный\s*[-:]\s*(.+?)(?:\n|$)',
                    r'Номер\s*[-:]\s*(.+?)(?:\n|$)',
                    # Поиск номеров телефона после "не предоставил сопроводительного письма"
                    r'не предоставил сопроводительного письма.*?(\+?992[0-9]{9})',
                    r'не предоставил сопроводительного письма.*?(\+?[0-9]{9,15})',
                    # Поиск номеров телефона в тексте
                    r'Текст сообщения:.*?(\+?992[0-9]{9})',
                    r'Текст сообщения:.*?(\+?[0-9]{9,15})',
                    r'(\+?992[0-9]{9})',
                    r'(\+?[0-9]{9,15})'
                ]

                for pattern in phone_patterns:
                    phone_match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
                    if phone_match:
                        candidate_phone = phone_match.group(1).strip()
                        # Проверяем что это похоже на телефон
                        if re.search(r'[0-9+]', candidate_phone) and len(candidate_phone.replace(' ', '').replace('-', '').replace('+', '')) >= 9:
                            phone = candidate_phone
                            break

            result = {
                'name': name,
                'email': email,
                'phone': phone,
                'message': applicant_message
            }

            # Отладочные сообщения убраны

            return result

        except Exception as e:
            print(f"Ошибка парсинга HTML: {e}")
            return {'name': None, 'email': None, 'phone': None}

    def extract_vacancy_title(self, subject):
        """Извлекает название вакансии из заголовка"""
        if ' - ' in subject:
            return subject.split(' - ', 1)[1].strip()
        return subject.replace('Отклик на вакансию', '').strip()

    async def get_or_create_vacancy(self, session, title):
        """Находит существующую вакансию или создает новую"""
        try:
            from sqlalchemy import select
            stmt = select(Vacancy).where(Vacancy.title == title)
            result = await session.execute(stmt)
            vacancy = result.scalar_one_or_none()

            is_new_vacancy = False
            if not vacancy:
                vacancy = Vacancy(title=title, description=f"Вакансия с сайта SomonTj: {title}")
                session.add(vacancy)
                await session.flush()  # Получаем ID без коммита
                print(f"Создана новая вакансия: {title}")
                is_new_vacancy = True

            return vacancy, is_new_vacancy
        except Exception as e:
            print(f"Ошибка при работе с вакансией: {e}")
            return None, False

    def extract_name(self, from_email, body):
        name_match = re.search(r'([А-Яа-я]+\s+[А-Яа-я]+)', body)
        if name_match:
            return name_match.group(1)

        email_name = re.search(r'(.+?)\s*<', from_email)
        if email_name:
            return email_name.group(1).strip()

        return from_email.split('@')[0]

