from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate


class UserCRUD:
    async def get_user_by_email(
        self, db: AsyncSession, *, email: str
    ) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        db_obj = User(
            email=user_in.email,
            full_name=user_in.full_name,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj