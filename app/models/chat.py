
from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio

class ChatType(Enum):
    TECH = "TECH"
    PERSONAL = "PERSONAL"
    EDUCATION = "EDUCATION"
    SUGGEST = "SUGGEST"
    CONTACT = "CONTACT"
    ETC = "ETC"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    ip: Mapped[str] = mapped_column(String(16), index=True)
    
    type: Mapped[ChatType] = mapped_column(SQLAlchemyEnum(ChatType), nullable=False)
    
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    portfolio: Mapped["Portfolio"] = relationship(back_populates="items")
    