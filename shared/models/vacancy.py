from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database.database import Base

class Vacancy(Base):
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("Application", back_populates="vacancy")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(500), nullable=True)
    attachment_filename = Column(String(255), nullable=True)
    gmail_message_id = Column(String(255), unique=True, nullable=False)
    applicant_message = Column(Text, nullable=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_processed = Column(Boolean, default=False)

    vacancy = relationship("Vacancy", back_populates="applications")