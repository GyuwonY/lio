import uuid
from typing import List
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.chat_message import ChatMessageType
from app.schemas.chat_message_schema import ChatMessage


class ChatSessionCreate(BaseModel):
    portfolio_id: uuid.UUID
    user_id: uuid.UUID


class ConversationTurn(BaseModel):
    input: str
    answer: str


class ChatContext(BaseModel):
    context: List[ConversationTurn] = Field(default_factory=list)


class ChatSessionInfo(BaseModel):
    chat_session_id: str
    context: List[ConversationTurn] = Field(default_factory=list)


class ChatSession(BaseModel):
    id: uuid.UUID
    session_id: str
    type: ChatMessageType
    portfolio_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    messages: List[ChatMessage] = []


class ChatSessionCreateResponse(BaseModel):
    chat_session_id: uuid.UUID
