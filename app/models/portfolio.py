import uuid
from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.portfolio_item import PortfolioItem
    from app.models.chat_session import ChatSession


class PortfolioStatus(Enum):
    DELETED = "DELETED"
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DRAFT_QNA = "DRAFT_QNA"
    PENDING_QNA = "PENDING_QNA"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class PortfolioSourceType(Enum):
    PDF = "PDF"
    TEXT = "TEXT"


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    theme:  Mapped[Optional[str]] = mapped_column(String, nullable=True)

    status: Mapped[PortfolioStatus] = mapped_column(
        SQLAlchemyEnum(PortfolioStatus), nullable=False, default=PortfolioStatus.DRAFT
    )

    source_type: Mapped[PortfolioSourceType] = mapped_column(
        SQLAlchemyEnum(PortfolioSourceType), nullable=False
    )
    source_url: Mapped[str] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="portfolios")
    items: Mapped[List["PortfolioItem"]] = relationship(back_populates="portfolio", order_by="desc(PortfolioItem.start_date)")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        back_populates="portfolio"
    )
