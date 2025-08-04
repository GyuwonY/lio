from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.models.qna import QnA
from app.schemas.qna import QnAUpdate
from app.models.user import User


class QnACRUD:
    async def get_qna_by_id(self, db: AsyncSession, *, qna_id: int) -> Optional[QnA]:
        result = await db.execute(select(QnA).filter(QnA.id == qna_id))
        return result.scalars().first()

    async def get_qnas_by_user(self, db: AsyncSession, *, user: User) -> List[QnA]:
        result = await db.execute(select(QnA).filter(QnA.user_id == user.id))
        return list(result.scalars().all())

    async def create_qna(
        self, db: AsyncSession, *, question: str, answer: str, user: User
    ) -> QnA:
        db_qna = QnA(question=question, answer=answer, user_id=user.id)
        db.add(db_qna)
        await db.commit()
        await db.refresh(db_qna)
        return db_qna

    async def update_qna(self, db: AsyncSession, *, db_obj: QnA, obj_in: QnAUpdate) -> QnA:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
