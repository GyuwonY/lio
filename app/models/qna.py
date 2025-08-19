from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import Integer, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.session import Base
from app.models.user import User


class QnAStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DELETED = "DELETED"


class QnA(Base):
    __tablename__ = "qnas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    question: Mapped[str] = mapped_column(Text, nullable=False)

    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    embedding = mapped_column(Vector(768), nullable=True)

    status: Mapped[QnAStatus] = mapped_column(
        Enum(QnAStatus), default=QnAStatus.PENDING, nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="qnas")
