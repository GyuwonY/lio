from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional
from app.models.portfolio_item import PortfolioItemType


# PortfolioItem 관련 스키마
class PortfolioItemBase(BaseModel):
    type: PortfolioItemType
    topic: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    content: str
    tech_stack: Optional[List[str]] = None


class PortfolioItemCreate(PortfolioItemBase):
    pass

class PortfolioItemsCreate(BaseModel):
    portfolio_id: int
    portfolio_items: List[PortfolioItemCreate]


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
    tech_stack: Optional[List[str]] = None


class PortfolioItemsUpdate(BaseModel):
    items: List[PortfolioItemUpdate]


class PortfolioItemDelete(BaseModel):
    portfolio_item_ids: List[int]
