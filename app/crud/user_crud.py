import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from fastapi import Depends

from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.db.session import get_db


class UserCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_user_by_email(self, *, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_user_by_id(self, *, user_id: uuid.UUID) -> Optional[User]:
        result = await self.db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    async def create_user(self, *, user_in: UserCreate) -> User:
        db_obj = User(
            email=user_in.email,
            full_name=user_in.full_name,
        )
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
