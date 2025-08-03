from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate

async def get_user_by_email(db: AsyncSession, *, email: str) -> Optional[User]:
    """
    이메일을 사용하여 데이터베이스에서 사용자를 비동기적으로 조회합니다.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, *, user_in: UserCreate) -> User:
    """
    새로운 사용자를 데이터베이스에 비동기적으로 생성합니다.
    """
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
