import logging
from typing import Optional
from shared.services.document_extractor import DocumentTextExtractor
from shared.services.gemini_service import GeminiService
from shared.models.vacancy import Application, Vacancy

logger = logging.getLogger(__name__)

class ResumeSummaryService:
    """Service for generating resume summaries"""

    def __init__(self):
        self.document_extractor = DocumentTextExtractor()
        self.gemini_service = GeminiService()

    async def generate_summary_for_application(self, application: Application, vacancy: Optional[Vacancy] = None) -> Optional[str]:
        """
        Generate summary for application if it has a resume file

        Args:
            application: Application object with file information
            vacancy: Optional vacancy object for context

        Returns:
            Generated HTML summary or None
        """
        # Check if application has a file
        if not application.file_path and not application.attachment_filename:
            logger.info(f"Application {application.id} has no resume file, skipping summary generation")
            return None

        # Check if file format is supported
        filename = application.attachment_filename or application.file_path
        if not self.document_extractor.is_supported_format(filename):
            logger.warning(f"Unsupported file format for application {application.id}: {filename}")
            return None

        # Extract text from resume file
        resume_text = None
        if application.file_path:
            resume_text = self.document_extractor.extract_text_from_file(application.file_path)

        if not resume_text:
            logger.error(f"Failed to extract text from resume file for application {application.id}")
            return None

        # Prepare data for Gemini API
        cover_letter_text = application.applicant_message or ""
        vacancy_title = vacancy.title if vacancy else ""

        # Generate summary using Gemini API
        try:
            summary = self.gemini_service.generate_resume_summary(
                resume_text=resume_text,
                cover_letter_text=cover_letter_text,
                vacancy_title=vacancy_title
            )

            if summary:
                logger.info(f"Successfully generated summary for application {application.id}")
                return summary
            else:
                logger.error(f"Gemini API returned empty summary for application {application.id}")
                return None

        except Exception as e:
            logger.error(f"Error generating summary for application {application.id}: {str(e)}")
            return None