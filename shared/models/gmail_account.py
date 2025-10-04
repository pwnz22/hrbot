from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from shared.database.database import Base


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id = Column(String, primary_key=True)  # "main", "parliament888", etc.
    name = Column(String, nullable=False)
    credentials_path = Column(String, nullable=False)
    token_path = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=True)  # Привязка к пользователю

    # Relationship
    user = relationship("TelegramUser", back_populates="gmail_accounts")
    vacancies = relationship("Vacancy", back_populates="gmail_account")
