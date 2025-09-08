from typing import List
import uuid
import redis.asyncio as aioredis
from fastapi import Depends

from app.db.session import get_redis_client
from app.schemas.chat_session_schema import ChatContext, ConversationTurn
from app.crud.chat_session_crud import ChatSessionCRUD
from app.models.chat_session import ChatSession


class ChatSessionService:
    def __init__(
        self,
        redis_client: aioredis.Redis = Depends(get_redis_client),
        chat_session_crud: ChatSessionCRUD = Depends(),
    ):
        self.redis_client = redis_client
        self.chat_session_crud = chat_session_crud
        self.context_expire_time = 3600

    async def create_session(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChatSession:
        session_id = f"{str(portfolio_id)}:{str(uuid.uuid4())}"

        chat_session = await self.chat_session_crud.create_chat_session(
            user_id=user_id,
            portfolio_id=portfolio_id,
            session_id=session_id,
        )

        session_data = ChatContext()
        await self.redis_client.set(
            f"session:{session_id}",
            session_data.model_dump_json(),
            ex=self.context_expire_time,
        )
        return chat_session

    async def get_session(self, session_id: str) -> ChatContext | None:
        chat_session = await self.chat_session_crud.get_chat_session_by_session_id(
            session_id=session_id
        )
        if not chat_session:
            raise

        session_data_str = await self.redis_client.get(f"session:{session_id}")
        if session_data_str:
            return ChatContext.model_validate_json(session_data_str)
        return None

    async def update_session(self, session_id: str, context: List[ConversationTurn]):
        session_data = ChatContext(context=context)
        await self.redis_client.set(
            f"session:{session_id}",
            session_data.model_dump_json(),
            ex=self.context_expire_time,
        )
