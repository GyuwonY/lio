from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.chat_session import ChatSession, ChatType
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.schemas.chat_schema import ChatCreate


class ChatCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def create_chat(
        self, *, chat_in: ChatCreate, user: User, answer: str, session_id: str, type: ChatType
    ) -> ChatMessage:
        """
        Chat 데이터를 생성합니다. session_id를 기준으로 세션을 찾거나 생성하고,
        새로운 메시지를 추가합니다.
        """
        session = await self.db.execute(
            select(ChatSession).filter(ChatSession.session_id == session_id)
        ).scalar_one_or_none()

        if not session:
            session = ChatSession(
                session_id=session_id,
                type=type,
                portfolio_id=chat_in.portfolio_id,
                user_id=user.id,
            )
            self.db.add(session)
            await self.db.flush()

        db_chat_message = ChatMessage(
            chat_session_id=session.id,
            question=chat_in.question,
            answer=answer,
        )
        self.db.add(db_chat_message)
        await self.db.commit()
        await self.db.refresh(db_chat_message)
        return db_chat_message