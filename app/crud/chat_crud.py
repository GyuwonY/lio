from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.chat import Chat
from app.models.user import User
from app.schemas.chat_schema import ChatCreate


class ChatCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def create_chat(self, *, chat_in: ChatCreate, user: User, answer: str) -> Chat:
        """
        Chat 데이터를 생성합니다.
        """
        db_chat = Chat(
            question=chat_in.question,
            answer=answer,
            user_id=user.id,
            portfolio_id=chat_in.portfolio_id
        )
        self.db.add(db_chat)
        await self.db.commit()
        await self.db.refresh(db_chat)
        return db_chat
