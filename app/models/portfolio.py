from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.portfolio_item import PortfolioItem


class Portfolio(Base):
    """포트폴리오 제출 세션 또는 원본 문서를 나타내는 모델"""
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 어떤 종류의 제출이었는지 명시 (예: 'pdf', 'text')
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # PDF의 경우 파일 경로, 텍스트의 경우 고유 식별자 등을 저장
    source_identifier: Mapped[str] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="portfolios")
    # Portfolio 하나에 여러 PortfolioItem이 연결 (one-to-many)
    items: Mapped[List["PortfolioItem"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )

