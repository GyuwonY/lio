import uuid
from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio
    from app.models.user import User
    from app.models.chat_message import ChatMessage


class ChatType(Enum):
    TECH = "TECH"
    PERSONAL = "PERSONAL"
    EDUCATION = "EDUCATION"
    SUGGEST = "SUGGEST"
    CONTACT = "CONTACT"
    ETC = "ETC"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    
    type: Mapped[ChatType] = mapped_column(SQLAlchemyEnum(ChatType), nullable=False)
    
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    portfolio: Mapped["Portfolio"] = relationship(back_populates="chat_sessions")
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[List["ChatMessage"]] = relationship(back_populates="chat_session")
