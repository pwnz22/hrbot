import os
import logging
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    """Service for working with Google Gemini API"""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')

    def generate_resume_summary(self, resume_text: str, cover_letter_text: str = "", vacancy_title: str = "") -> Optional[str]:
        """
        Generate HTML summary for resume using Gemini API

        Args:
            resume_text: Extracted text from resume file
            cover_letter_text: Text from cover letter/applicant message
            vacancy_title: Title of the vacancy

        Returns:
            Generated HTML summary or None if generation failed
        """
        prompt = self._build_prompt(resume_text, cover_letter_text, vacancy_title)

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating resume summary: {str(e)}")
            return None

    def _build_prompt(self, resume_text: str, cover_letter_text: str, vacancy_title: str) -> str:
        """Build prompt for Gemini API"""
        prompt = """Ты — опытный HR-аналитик. Твоя задача — проанализировать резюме и сопроводительное письмо кандидата и составить краткое, структурированное саммари.

Проанализируй предоставленные ниже тексты и верни результат в формате для Telegram (с HTML разметкой) со следующими данными:

📋 <b>Вакансия:</b> [название вакансии]

👤 <b>Кандидат:</b> [полное имя]
📧 <b>Email:</b> [email или "не указан"]
📱 <b>Телефон:</b> [телефон или "не указан"]
🔗 <b>GitHub:</b> [ссылка или "не указан"]

📝 <b>Краткое резюме:</b>
[3-4 предложения о ключевых сильных сторонах и опыте кандидата в контексте пользы для компании]

🛠 <b>Ключевые навыки:</b>
• [навык 1]
• [навык 2]
• [навык 3]
• [навык 4]
• [навык 5]

⏰ <b>Опыт работы:</b> [X лет]

🎓 <b>Образование:</b>
[краткое описание основного образования]

⚠️ <b>Потенциальные риски:</b>
[если есть красные флаги - перечисли, если нет - не включай этот блок]

❓ <b>Вопросы для собеседования:</b>

1. <b>Вопрос:</b> [вопрос по ключевому навыку или опыту]
   <i>Ответ:</i> [краткий ожидаемый ответ на основе резюме]

2. <b>Вопрос:</b> [вопрос про технологию/инструмент из резюме]
   <i>Ответ:</i> [краткий ожидаемый ответ]

3. <b>Вопрос:</b> [вопрос про предыдущий опыт работы]
   <i>Ответ:</i> [краткий ожидаемый ответ]

4. <b>Вопрос:</b> [вопрос про проект из резюме]
   <i>Ответ:</i> [краткий ожидаемый ответ]

5. <b>Вопрос:</b> [вопрос на углубление знаний]
   <i>Ответ:</i> [краткий ожидаемый ответ]

6. <b>Вопрос:</b> [вопрос про soft skills]
   <i>Ответ:</i> [краткий ожидаемый ответ]

7. <b>Вопрос:</b> [вопрос про архитектуру/best practices]
   <i>Ответ:</i> [краткий ожидаемый ответ]

8. <b>Вопрос:</b> [вопрос про инструменты разработки]
   <i>Ответ:</i> [краткий ожидаемый ответ]

9. <b>Вопрос:</b> [вопрос про командную работу]
   <i>Ответ:</i> [краткий ожидаемый ответ]

10. <b>Вопрос:</b> [вопрос про мотивацию/планы]
    <i>Ответ:</i> [краткий ожидаемый ответ]

Примечание: Вопросы должны быть релевантны навыкам и опыту кандидата из резюме. Ответы — это ожидаемые правильные ответы на основе информации из резюме.

ВАЖНО: Используй только базовые HTML теги для Telegram: <b>, <i>, <u>, <code>, <pre>. НЕ используй сложную HTML разметку!

Вот данные для анализа:"""

        if vacancy_title:
            prompt += f"\n\n<vacancy_title>\n{vacancy_title}\n</vacancy_title>"

        prompt += f"\n\n<resume>\n{resume_text}\n</resume>"

        if cover_letter_text:
            prompt += f"\n\n<cover_letter>\n{cover_letter_text}\n</cover_letter>"

        return prompt