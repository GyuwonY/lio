from typing import List
import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.chat import ChatType

class ChatBase(BaseModel):
    question: str


class ChatCreate(ChatBase):
    email: str
    portfolio_id: uuid.UUID


class Chat(ChatBase):
    id: uuid.UUID
    user_id: uuid.UUID
    answer: str | None = None
    created_at: datetime
    type: ChatType

class ChatResponse(BaseModel):
    answer: str
    
    
class GraphStateQuery(BaseModel):
    query: str
    embedding: List[float]  = Field(default_factory=list)
