from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.models.qna import QnA
from app.schemas.qna import QnAUpdate
from app.models.user import User

async def get_qna_by_id(db: AsyncSession, *, qna_id: int) -> Optional[QnA]:
    """ID로 QnA를 비동기적으로 조회합니다."""
    result = await db.execute(select(QnA).filter(QnA.id == qna_id))
    return result.scalars().first()

async def get_qnas_by_owner(db: AsyncSession, *, owner: User) -> List[QnA]:
    """특정 사용자가 소유한 모든 QnA를 비동기적으로 조회합니다."""
    result = await db.execute(select(QnA).filter(QnA.owner_id == owner.id))
    return result.scalars().all()

async def create_qna(db: AsyncSession, *, question: str, answer: str, owner: User) -> QnA:
    """
    새로운 QnA를 데이터베이스에 비동기적으로 생성합니다.
    """
    db_qna = QnA(question=question, answer=answer, owner_id=owner.id)
    db.add(db_qna)
    await db.commit()
    await db.refresh(db_qna)
    return db_qna

async def update_qna(db: AsyncSession, *, db_obj: QnA, obj_in: QnAUpdate) -> QnA:
    """
    기존 QnA를 비동기적으로 수정합니다.
    """
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
