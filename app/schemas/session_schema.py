import uuid
from typing import Any, List
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    portfolio_id: uuid.UUID


class ConversationTurn(BaseModel):
    input: str
    answer: str


class SessionData(BaseModel):
    context: List[ConversationTurn] = Field(default_factory=list)
