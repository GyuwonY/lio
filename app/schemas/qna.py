from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

from app.models.qna import QnAStatus

class QnABase(BaseModel):
    """공통 QnA 필드"""
    question: str
    answer: Optional[str] = None

class QnACreate(BaseModel):
    """LLM을 통한 QnA 생성을 요청하는 스키마"""
    portfolio_ids: List[int]

class QnAUpdate(BaseModel):
    """사용자가 QnA를 수정하는 스키마"""
    question: Optional[str] = None
    answer: Optional[str] = None
    status: Optional[QnAStatus] = None

class QnARead(QnABase):
    """QnA 조회를 위한 스키마 (API 응답용)"""
    id: int
    status: QnAStatus
    owner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
