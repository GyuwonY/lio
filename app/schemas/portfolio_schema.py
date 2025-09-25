import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional
from app.models.portfolio import PortfolioStatus
from app.schemas.portfolio_item_schema import PortfolioItemCreate, PortfolioItemRead


class PortfolioBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: Optional[str]
    theme: Optional[str]
    


class PortfolioCreateFromText(PortfolioBase):
    """텍스트 입력을 통한 포트폴리오 생성을 위한 요청 스키마"""
    text_items: List[PortfolioItemCreate]


class PortfolioCreateWithPdf(PortfolioBase):
    """PDF 업로드를 통한 포트폴리오 생성을 위한 내부 사용 스키마"""

    file_path: str
    name: Optional[str]


class PortfolioCreationResponse(PortfolioBase):
    """포트폴리오 생성 요청 시 즉시 반환되는 응답 스키마"""

    id: uuid.UUID
    status: PortfolioStatus


class PortfolioReadWithoutItems(PortfolioBase):
    """포트폴리오 조회를 위한 스키마 (API 응답용)"""

    id: uuid.UUID
    user_id: uuid.UUID
    status: PortfolioStatus
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime


class PortfolioRead(PortfolioBase):
    """포트폴리오 조회를 위한 스키마 (API 응답용)"""

    id: uuid.UUID
    user_id: uuid.UUID
    status: PortfolioStatus
    source_type: str
    source_url: Optional[str] = None
    created_at: datetime
    items: List[PortfolioItemRead] = []


class PublishedPortfolioRead(PortfolioBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: PortfolioStatus
    created_at: datetime
    items: List[PortfolioItemRead] = []
    first_name: Optional[str]
    last_name: Optional[str]
    address: Optional[str]
    job: Optional[str]


class PortfolioUpdate(PortfolioBase):
    pass


class PortfolioConfirm(BaseModel):
    portfolio_id: uuid.UUID


class UploadURLResponse(BaseModel):
    upload_url: str
    file_path: str


class PortfolioDelete(BaseModel):
    portfolio_item_ids: List[uuid.UUID]
