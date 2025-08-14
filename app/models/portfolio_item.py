from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLAlchemyEnum
from app.db.session import Base
from datetime import datetime
from app.schemas.portfolio_schema import PortfolioType
from pgvector.sqlalchemy import Vector
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.portfolio import Portfolio


class PortfolioItem(Base):
    """개별 포트폴리오 항목을 나타내는 모델"""
    __tablename__ = "portfolio_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), nullable=False)

    item_type: Mapped[PortfolioType] = mapped_column(SQLAlchemyEnum(PortfolioType), nullable=False)
    
    topic: Mapped[str] = mapped_column(String(255), nullable=True)
    period: Mapped[str] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    embedding = mapped_column(Vector(768))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    portfolio: Mapped["Portfolio"] = relationship(back_populates="items")
    