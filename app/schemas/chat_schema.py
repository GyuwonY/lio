from typing import List
import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.chat_session import ChatType


class ChatCreate(BaseModel):
    question: str
    email: str
    portfolio_id: uuid.UUID
    type: ChatType


class ChatMessage(BaseModel):
    id: uuid.UUID
    question: str
    answer: str | None = None
    created_at: datetime
    chat_session_id: uuid.UUID

    class Config:
        orm_mode = True


class ChatSession(BaseModel):
    id: uuid.UUID
    session_id: str
    type: ChatType
    portfolio_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    messages: List[ChatMessage] = []

    class Config:
        orm_mode = True


class ChatResponse(BaseModel):
    answer: str
    session_id: str


class GraphStateQuery(BaseModel):
    query: str
    embedding: List[float] = Field(default_factory=list)