from sqlalchemy.future import select
import uuid
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat_session import ChatSession


class ChatSessionCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def create_chat_session(
        self, *, user_id: uuid.UUID, portfolio_id: uuid.UUID, session_id: str
    ) -> ChatSession:
        db_obj = ChatSession(
            user_id=user_id, portfolio_id=portfolio_id, session_id=session_id
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_chat_session_by_session_id(self, *, session_id: str) -> ChatSession | None:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        return result.scalars().first()