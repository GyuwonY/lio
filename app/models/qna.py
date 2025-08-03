from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base

class QnAStatus(enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"

class QnA(Base):
    __tablename__ = "qnas"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    status = Column(Enum(QnAStatus), default=QnAStatus.DRAFT, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="qnas")

# User 모델에 qnas 관계 추가
from app.models.user import User
User.qnas = relationship("QnA", order_by=QnA.id, back_populates="owner")
