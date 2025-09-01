
import uuid
import redis.asyncio as aioredis
from fastapi import Depends
from app.db.session import get_redis_client
from app.schemas.session_schema import ConversationTurn, SessionData


class SessionService:
    def __init__(
        self,
        redis_client: aioredis.Redis = Depends(get_redis_client),
    ):
        self.redis_client = redis_client
        self.context_expire_time = 3600


    async def create_session(self, portfolio_id: uuid.UUID) -> str:
        session_id = f"{portfolio_id}:{str(uuid.uuid4())}"
        session_data = SessionData()
        await self.redis_client.set(
            f"session:{session_id}",
            session_data.model_dump_json(),
            ex=self.context_expire_time,
        )
        return session_id


    async def get_session(self, session_id: str) -> SessionData | None:
        session_data_str = await self.redis_client.get(f"session:{session_id}")
        if session_data_str:
            return SessionData.model_validate_json(session_data_str)
        return None


    async def update_session_context(self, session_id: str, new_context: ConversationTurn) -> None:
        session_data = await self.get_session(session_id)
        if session_data:
            session_data.context.append(new_context)
            await self.redis_client.set(
                f"session:{session_id}",
                session_data.model_dump_json(),
                ex=self.context_expire_time,
            )


    async def delete_session(self, session_id: str) -> None:
        await self.redis_client.delete(f"session:{session_id}")
