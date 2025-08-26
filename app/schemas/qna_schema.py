import uuid
from pydantic import BaseModel
from typing import List

from app.models.qna import QnAStatus


class QnABase(BaseModel):
    question: str
    answer: str


class QnAUpdate(BaseModel):
    id: uuid.UUID
    question: str
    answer: str


class QnARead(QnABase):
    id: uuid.UUID
    status: QnAStatus
    portfolio_item_id: uuid.UUID


class QnACreate(QnABase):
    portfolio_item_id: uuid.UUID

class QnAsUpdate(BaseModel):
    qnas: List[QnAUpdate]

class QnAsDelete(BaseModel):
    qna_ids: List[uuid.UUID]

class QnAsConfirm(BaseModel):
    qna_ids: List[uuid.UUID]
