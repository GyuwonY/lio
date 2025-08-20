from pydantic import BaseModel
from typing import List

from app.models.qna import QnAStatus


class QnABase(BaseModel):
    question: str
    answer: str


class QnAUpdate(BaseModel):
    id: int
    question: str
    answer: str


class QnARead(QnABase):
    id: int
    status: QnAStatus
    portfolio_item_id: int


class QnACreate(QnABase):
    portfolio_item_id: int

class QnAsUpdate(BaseModel):
    qnas: List[QnAUpdate]
