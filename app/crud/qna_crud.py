from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert
from typing import List
from fastapi import Depends

from app.models.qna import QnA, QnAStatus
from app.schemas.qna_schema import QnACreate
from app.db.session import get_db
from app.models.portfolio_item import PortfolioItem


class QnACRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db


    async def get_qnas_by_portfolio_id(self, *, portfolio_id: int, user_id: int) -> List[QnA]:
        stmt = (
            select(QnA)
            .join(PortfolioItem, QnA.portfolio_item_id == PortfolioItem.id)
            .where(
                PortfolioItem.portfolio_id == portfolio_id,
                QnA.status != QnAStatus.DELETED,
                QnA.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def bulk_create_qnas(
        self, *, qna_list: List[QnACreate], user_id: int
    ) -> List[QnA]:
        if not qna_list:
            return []
            
        qnas_data = [
            {
                "question": qna.question,
                "answer": qna.answer,
                "portfolio_item_id": qna.portfolio_item_id,
                "user_id": user_id,
                "status": QnAStatus.PENDING,
            }
            for qna in qna_list
        ]
        
        result = await self.db.execute(insert(QnA).values(qnas_data).returning(QnA))
        return list(result.scalars().all())


    async def get_qnas_by_ids(self, *, ids: List[int], user_id: int) -> List[QnA]:
        result = await self.db.execute(
            select(QnA)
            .where(QnA.id.in_(ids), QnA.user_id == user_id)
        )
        return list(result.scalars().all())
        