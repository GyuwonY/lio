import uuid
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat_message import ChatMessage, ChatMessageType


class ChatMessageCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def create_chat_message(
        self,
        *,
        chat_session_id: uuid.UUID,
        question: str,
        answer: str,
        type: ChatMessageType,
    ) -> ChatMessage:
        db_obj = ChatMessage(
            chat_session_id=chat_session_id,
            question=question,
            answer=answer,
            type=type,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
