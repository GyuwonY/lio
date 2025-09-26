import uuid
from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional
from app.models.portfolio_item import PortfolioItemType


# PortfolioItem 관련 스키마
class PortfolioItemBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: PortfolioItemType
    topic: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    content: str
    tech_stack: Optional[List[str]] = None


class PortfolioItemCreate(PortfolioItemBase):
    pass


class PortfolioItemsCreate(BaseModel):
    portfolio_id: uuid.UUID
    portfolio_items: List[PortfolioItemCreate]


class PortfolioItemRead(PortfolioItemBase):
    id: uuid.UUID
    portfolio_id: uuid.UUID
    created_at: datetime


class PortfolioItemUpdate(BaseModel):
    id: uuid.UUID
    type: PortfolioItemType
    topic: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    content: str
    tech_stack: Optional[List[str]] = None


class PortfolioItemsUpdate(BaseModel):
    items: List[PortfolioItemUpdate]


class PortfolioItemDelete(BaseModel):
    portfolio_item_ids: List[uuid.UUID]


class PortfolioItemLLMInput(BaseModel):
    type: str
    topic: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    content: str
    tech_stack: Optional[List[str]]
