from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class VacancyBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None

class VacancyCreate(VacancyBase):
    gmail_message_id: str

class VacancyResponse(VacancyBase):
    id: int
    gmail_message_id: str
    created_at: datetime
    is_processed: bool

    class Config:
        from_attributes = True