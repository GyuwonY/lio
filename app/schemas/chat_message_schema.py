from typing import List
import uuid
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessageCreate(BaseModel):
    question: str
    email: str
    portfolio_id: uuid.UUID


class ChatMessage(BaseModel):
    id: uuid.UUID
    question: str
    answer: str | None = None
    created_at: datetime
    chat_session_id: uuid.UUID


class ChatMessageResponse(BaseModel):
    answer: str
    session_id: str


class GraphStateQuery(BaseModel):
    query: str
    embedding: List[float] = Field(default_factory=list)
