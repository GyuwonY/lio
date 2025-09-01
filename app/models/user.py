import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.chatbot_setting import ChatbotSetting
    from app.models.portfolio import Portfolio
    from app.models.chat_session import ChatSession


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )

    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    remain_chat_cnt: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    portfolios: Mapped[List["Portfolio"]] = relationship(back_populates="user")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="user")
    chatbot_setting: Mapped["ChatbotSetting"] = relationship(back_populates="user")
