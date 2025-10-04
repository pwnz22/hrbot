from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from shared.database.database import Base


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account_id = Column(String, unique=True, nullable=False, index=True)  # "pwnz888", "parliament888", etc.
    name = Column(String, nullable=False)
    credentials_path = Column(String, nullable=False)
    token_path = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=True)

    # Relationship
    user = relationship("TelegramUser", back_populates="gmail_accounts")
    vacancies = relationship("Vacancy", back_populates="gmail_account")
