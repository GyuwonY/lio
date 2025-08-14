from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from enum import Enum
from typing import List, Optional

class PortfolioType(str, Enum):
    INTRODUCTION = "INTRODUCTION"
    EXPERIENCE = "EXPERIENCE"
    PROJECT = "PROJECT"
    SKILLS = "SKILLS"
    EDUCATION = "EDUCATION"

# PortfolioItem 관련 스키마
class PortfolioItemBase(BaseModel):
    item_type: PortfolioType
    topic: Optional[str] = None
    period: Optional[str] = None
    content: str

class PortfolioItemCreate(PortfolioItemBase):
    pass

class PortfolioItemRead(PortfolioItemBase):
    id: int
    portfolio_id: int
    created_at: datetime

# Portfolio (컨테이너) 관련 스키마
class PortfolioBase(BaseModel):
    pass

class PortfolioCreate(PortfolioBase):
    """포트폴리오 생성을 위한 요청 스키마"""
    file_url: Optional[str] = None
    text_items: Optional[List[PortfolioItemCreate]] = None

    @field_validator('text_items', mode='before')
    def check_exclusive_fields(cls, v, values):
        if values.data.get('file_url') and v:
            raise ValueError("file_url과 text_items는 함께 사용할 수 없습니다.")
        if not values.data.get('file_url') and not v:
            raise ValueError("file_url 또는 text_items 중 하나는 반드시 필요합니다.")
        return v

class PortfolioRead(PortfolioBase):
    """포트폴리오 조회를 위한 스키마 (API 응답용)"""
    id: int
    user_id: int
    source_type: str
    source_identifier: Optional[str] = None
    created_at: datetime
    items: List[PortfolioItemRead] = []

# 기타 유틸리티 스키마
class UploadURLResponse(BaseModel):
    upload_url: str
    file_path: str