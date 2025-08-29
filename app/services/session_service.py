
import uuid
from typing import Any
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
        self.context_expire_time = 3600  # 60 minutes

    async def create_session(self, portfolio_id: uuid.UUID) -> str:
        session_id = f"{portfolio_id}:{str(uuid.uuid4())}"
        session_data = SessionData()  # Pydantic 모델 인스턴스 생성
        await self.redis_client.set(
            f"session:{session_id}",
            session_data.model_dump_json(),  # JSON 문자열로 변환하여 저장
            ex=self.context_expire_time,
        )
        return session_id

    async def get_session(self, session_id: str) -> SessionData | None:
        session_data_str = await self.redis_client.get(f"session:{session_id}")
        if session_data_str:
            return SessionData.model_validate_json(session_data_str)  # JSON 문자열을 Pydantic 모델로 파싱
        return None

    async def update_session_context(self, session_id: str, new_context: ConversationTurn) -> None:
        """
        세션의 채팅 컨텍스트를 업데이트합니다.
        """
        session_data = await self.get_session(session_id)
        if session_data:
            session_data.context.append(new_context)
            await self.redis_client.set(
                f"session:{session_id}",
                session_data.model_dump_json(),
                ex=self.context_expire_time,
            )

    async def delete_session(self, session_id: str) -> None:
        """
        세션을 삭제합니다.
        """
        await self.redis_client.delete(f"session:{session_id}")

    async def get_session_context(self, session_id: str) -> list[ConversationTurn] | None:
        """
        세션의 채팅 컨텍스트를 가져옵니다.
        """
        session_data = await self.get_session(session_id)
        if session_data:
            return session_data.context
        return None
