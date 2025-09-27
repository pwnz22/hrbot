from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class VacancyBase(BaseModel):
    title: str
    description: Optional[str] = None

class VacancyCreate(VacancyBase):
    pass

class VacancyResponse(VacancyBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    attachment_filename: Optional[str] = None
    applicant_message: Optional[str] = None
    vacancy_id: Optional[int] = None
    summary: Optional[str] = None

class ApplicationCreate(ApplicationBase):
    gmail_message_id: str

class ApplicationResponse(ApplicationBase):
    id: int
    gmail_message_id: str
    created_at: datetime
    is_processed: bool
    vacancy: Optional[VacancyResponse] = None

    class Config:
        from_attributes = True