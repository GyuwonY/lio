from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.models.portfolio import PortfolioStatus
from app.schemas.portfolio_item_schema import (
    PortfolioItemCreate,
    PortfolioItemRead,
)


class PortfolioBase(BaseModel):
    pass


class PortfolioCreateFromText(PortfolioBase):
    """텍스트 입력을 통한 포트폴리오 생성을 위한 요청 스키마"""
    name: Optional[str]
    text_items: List[PortfolioItemCreate]


class PortfolioCreateWithPdf(PortfolioBase):
    """PDF 업로드를 통한 포트폴리오 생성을 위한 내부 사용 스키마"""

    file_path: str


class PortfolioRead(PortfolioBase):
    """포트폴리오 조회를 위한 스키마 (API 응답용)"""

    id: int
    user_id: int
    status: PortfolioStatus
    name: Optional[str] = None
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime
    items: List[PortfolioItemRead] = []


class PortfolioUpdate(PortfolioBase):
    name: Optional[str] = None

class PortfolioConfirm(BaseModel):
    portfolio_id: int


class UploadURLResponse(BaseModel):
    upload_url: str
    file_path: str

