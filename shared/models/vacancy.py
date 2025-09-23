from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from shared.database.database import Base

class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    gmail_message_id = Column(String(255), unique=True, nullable=False)
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_processed = Column(Boolean, default=False)