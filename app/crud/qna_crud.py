from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from fastapi import Depends

from app.models.qna import QnA
from app.schemas.qna_schema import QnAUpdate
from app.models.user import User
from app.db.session import get_db


class QnACRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_qna_by_id(self, *, qna_id: int) -> Optional[QnA]:
        result = await self.db.execute(select(QnA).filter(QnA.id == qna_id))
        return result.scalars().first()

    async def get_qnas_by_user(self, *, user: User) -> List[QnA]:
        result = await self.db.execute(select(QnA).filter(QnA.user_id == user.id))
        return list(result.scalars().all())

    async def create_qna(self, *, question: str, answer: str, user: User) -> QnA:
        db_qna = QnA(question=question, answer=answer, user_id=user.id)
        self.db.add(db_qna)
        await self.db.commit()
        await self.db.refresh(db_qna)
        return db_qna

    async def update_qna(self, *, db_obj: QnA, obj_in: QnAUpdate) -> QnA:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
