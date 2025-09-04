import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatbotSetting(Base):
    __tablename__ = "chatbot_setting"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    tone_examples: Mapped[List[str]] = mapped_column(JSON, nullable=True)

    persona: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="chatbot_setting")
