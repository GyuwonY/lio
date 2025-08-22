from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.portfolio_item import PortfolioItem


class PortfolioStatus(Enum):
    DELETED = "DELETED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"


class PortfolioSourceType(Enum):
    PDF = "PDF"
    TEXT = "TEXT"


class Portfolio(Base):
    """포트폴리오 제출 세션 또는 원본 문서를 나타내는 모델"""

    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[PortfolioStatus] = mapped_column(
        SQLAlchemyEnum(PortfolioStatus), nullable=False, default=PortfolioStatus.PENDING
    )

    source_type: Mapped[PortfolioSourceType] = mapped_column(
        SQLAlchemyEnum(PortfolioSourceType), nullable=False
    )
    source_url: Mapped[str] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="portfolios")
    items: Mapped[List["PortfolioItem"]] = relationship(
        back_populates="portfolio"
    )
