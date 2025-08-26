import uuid
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


    async def get_qnas_by_portfolio_id(self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID) -> List[QnA]:
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
        self, *, qna_list: List[QnACreate], user_id: uuid.UUID
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


    async def get_qnas_by_ids(self, *, ids: List[uuid.UUID], user_id: uuid.UUID) -> List[QnA]:
        result = await self.db.execute(
            select(QnA)
            .where(QnA.id.in_(ids), QnA.user_id == user_id)
        )
        return list(result.scalars().all())
        

    async def search_qnas_by_portfolio_ids_and_embedding(
        self, *, portfolio_ids: List[uuid.UUID], embedding: List[float], user_id: uuid.UUID
    ) -> List[QnA]:
        """포트폴리오 ID 목록과 임베딩을 사용하여 유사한 QnA를 검색합니다."""
        result = await self.db.execute(
            select(QnA)
            .join(PortfolioItem, QnA.portfolio_item_id == PortfolioItem.id)
            .where(
                PortfolioItem.portfolio_id.in_(portfolio_ids),
                QnA.user_id == user_id,
                QnA.status == QnAStatus.CONFIRMED,
            )
            .order_by(QnA.question_embedding.cosine_distance(embedding))
            .limit(10)
        )
        return list(result.scalars().all())
        