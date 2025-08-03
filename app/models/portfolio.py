from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=True) # S3 등 외부 저장소 URL 또는 로컬 경로
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="portfolios")

# User 모델에 portfolios 관계 추가
from app.models.user import User
User.portfolios = relationship("Portfolio", order_by=Portfolio.id, back_populates="owner")
