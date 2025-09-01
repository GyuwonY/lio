import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.session import Base
from app.models.portfolio_item import PortfolioItem
from app.models.user import User


class QnAStatus(Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DELETED = "DELETED"


class QnA(Base):
    __tablename__ = "qnas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)

    answer: Mapped[str] = mapped_column(Text, nullable=False)

    embedding = mapped_column(Vector(768), nullable=True)

    status: Mapped[QnAStatus] = mapped_column(
        SQLAlchemyEnum(QnAStatus), default=QnAStatus.PENDING, nullable=False
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    portfolio_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_items.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="user")
    portfolio_item: Mapped[PortfolioItem] = relationship(back_populates="qnas")
