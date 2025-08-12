from typing import List, TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class ChatbotSetting(Base):
    __tablename__ = "chatbot_setting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    tone_examples: Mapped[List[str]] = mapped_column(JSON, nullable=True)

    persona: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="chatbot_setting")
