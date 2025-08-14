from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

from app.models.qna import QnAStatus


class QnABase(BaseModel):
    question: str
    answer: Optional[str] = None


class QnACreate(BaseModel):
    portfolio_ids: List[int]


class QnAUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    status: Optional[QnAStatus] = None


class QnARead(QnABase):
    id: int
    status: QnAStatus
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
