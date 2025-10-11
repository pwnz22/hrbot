"""
Utility functions for formatting application data consistently across handlers.
"""
from shared.models.vacancy import Application, Vacancy


def format_application_details(
    application: Application,
    vacancy: Vacancy | None,
    include_description: bool = False
) -> str:
    """
    Format application details consistently.

    Args:
        application: Application model instance
        vacancy: Vacancy model instance (can be None)
        include_description: Whether to include processing description

    Returns:
        Formatted text string with HTML markup
    """
    status = "✅ Обработан" if application.is_processed else "❌ Не обработан"

    text = f"👤 <b>{application.name}</b>\n\n"
    text += f"📋 Вакансия: {vacancy.title if vacancy else 'Неизвестно'}\n"
    text += f"📧 Email: {application.email or 'Не указан'}\n"
    text += f"📱 Телефон: {application.phone or 'Не указан'}\n"
    text += f"🏷️ Статус: {status}\n"
    text += f"📅 Дата отклика: {application.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"

    if application.applicant_message:
        text += f"💬 <b>Сообщение от кандидата:</b>\n{application.applicant_message}\n\n"

    if include_description:
        if application.processing_description:
            text += f"📝 <b>Описание обработки:</b>\n{application.processing_description}\n\n"
        else:
            text += "📝 <i>Описание обработки отсутствует</i>\n\n"

    return text
