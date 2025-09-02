import uuid
from pydantic import BaseModel
from datetime import date, datetime
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
    tech_stack: Optional[List[str]] = None


class PortfolioItemCreate(PortfolioItemBase):
    pass


class PortfolioItemRead(PortfolioItemBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    created_at: datetime


class PortfolioItemUpdate(BaseModel):
    id: uuid.UUID
    type: PortfolioItemType
    topic: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    content: str
    tech_stack: Optional[List[str]] = None


class PortfolioItemsUpdate(BaseModel):
    items: List[PortfolioItemUpdate]


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

    id: uuid.UUID
    user_id: uuid.UUID
    status: PortfolioStatus
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime
    items: List[PortfolioItemRead] = []


class PortfolioConfirm(BaseModel):
    portfolio_id: uuid.UUID


class UploadURLResponse(BaseModel):
    upload_url: str
    file_path: str


class PortfolioDelete(BaseModel):
    portfolio_item_ids: List[uuid.UUID]

class PortfolioItemLLMInput(BaseModel):
    type: str
    topic: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    content: str
    tech_stack: Optional[List[str]]
