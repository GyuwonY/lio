from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum, Date
from app.db.session import Base
from datetime import datetime, date
from typing import TYPE_CHECKING, List, Optional
from enum import Enum

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio


class PortfolioItemType(str, Enum):
    INTRODUCTION = "INTRODUCTION"
    EXPERIENCE = "EXPERIENCE"
    PROJECT = "PROJECT"
    SKILLS = "SKILLS"
    EDUCATION = "EDUCATION"


class PortfolioItemStatus(Enum):
    DELETED = "DELETED"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"


class PortfolioItem(Base):
    """개별 포트폴리오 항목을 나타내는 모델"""

    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id"), nullable=False
    )

    type: Mapped[PortfolioItemType] = mapped_column(
        SQLAlchemyEnum(PortfolioItemType), nullable=False
    )
    status: Mapped[PortfolioItemStatus] = mapped_column(
        SQLAlchemyEnum(PortfolioItemStatus),
        nullable=False,
        default=PortfolioItemStatus.PENDING,
    )

    topic: Mapped[str] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="items")
