from datetime import datetime
from typing import TYPE_CHECKING
import uuid
from app.db.session import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id"), nullable=False
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)

    answer: Mapped[str] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    chat_session: Mapped["ChatSession"] = relationship(back_populates="messages")