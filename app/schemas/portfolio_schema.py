from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.models.portfolio_item import PortfolioItemType
from app.models.portfolio import PortfolioStatus


# PortfolioItem 관련 스키마
class PortfolioItemBase(BaseModel):
    type: PortfolioItemType
    topic: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    content: str


class PortfolioItemCreate(PortfolioItemBase):
    pass


class PortfolioItemRead(PortfolioItemBase):
    id: int
    portfolio_id: int
    created_at: datetime


class PortfolioItemUpdate(BaseModel):
    id: int
    type: PortfolioItemType
    topic: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    content: str


class PortfolioItemsUpdate(BaseModel):
    items: List[PortfolioItemUpdate]


# Portfolio (컨테이너) 관련 스키마
class PortfolioBase(BaseModel):
    pass


class PortfolioCreateFromText(PortfolioBase):
    """텍스트 입력을 통한 포트폴리오 생성을 위한 요청 스키마"""

    text_items: List[PortfolioItemCreate]


class PortfolioCreateWithPdf(PortfolioBase):
    """PDF 업로드를 통한 포트폴리오 생성을 위한 내부 사용 스키마"""

    file_path: str


class PortfolioRead(PortfolioBase):
    """포트폴리오 조회를 위한 스키마 (API 응답용)"""

    id: int
    user_id: int
    status: PortfolioStatus
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime
    items: List[PortfolioItemRead] = []


class PortfolioConfirm(BaseModel):
    portfolio_id: int


# 기타 유틸리티 스키마
class UploadURLResponse(BaseModel):
    upload_url: str
    file_path: str
