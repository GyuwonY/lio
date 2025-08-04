from pydantic import BaseModel, ConfigDict
from datetime import datetime


class PortfolioBase(BaseModel):
    """공통 포트폴리오 필드"""

    file_name: str


class PortfolioCreate(PortfolioBase):
    """포트폴리오 생성을 위한 스키마"""

    pass


class PortfolioRead(PortfolioBase):
    """포트폴리오 조회를 위한 스키마 (API 응답용)"""

    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
