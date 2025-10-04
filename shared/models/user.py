from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database.database import Base
import enum


class RoleEnum(enum.Enum):
    """Роли пользователей"""
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class TelegramUser(Base):
    """Пользователи Telegram"""
    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    role = Column(SQLEnum(RoleEnum), default=RoleEnum.USER, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    gmail_accounts = relationship("GmailAccount", back_populates="user")

    def __repr__(self):
        return f"<TelegramUser(telegram_id={self.telegram_id}, username={self.username}, role={self.role})>"

    @property
    def is_admin(self):
        """Проверка является ли пользователь админом"""
        return self.role == RoleEnum.ADMIN

    @property
    def is_moderator(self):
        """Проверка является ли пользователь модератором"""
        return self.role == RoleEnum.MODERATOR

    @property
    def is_user(self):
        """Проверка является ли пользователь обычным пользователем"""
        return self.role == RoleEnum.USER

    def has_permission(self, permission: str) -> bool:
        """
        Проверка прав доступа

        Permissions:
        - view_applications: просмотр откликов
        - change_status: изменение статуса откликов
        - export_data: экспорт данных
        - parse_emails: парсинг писем
        - manage_accounts: управление Gmail аккаунтами
        - manage_users: управление пользователями
        """
        permissions_map = {
            RoleEnum.USER: [],
            RoleEnum.MODERATOR: [
                'view_applications',
                'change_status',
                'export_data',
                'parse_emails'
            ],
            RoleEnum.ADMIN: [
                'view_applications',
                'change_status',
                'export_data',
                'parse_emails',
                'manage_accounts',
                'manage_users'
            ]
        }

        return permission in permissions_map.get(self.role, [])
