import uuid
from typing import List
from fastapi import Depends
from sqlalchemy import literal_column, values, insert
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pgvector.sqlalchemy import Vector

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

    
    async def search_qnas_by_embeddings(
        self, *, portfolio_item_ids: List[uuid.UUID], embeddings: List[List[float]],
    ) -> List[QnA]:
        if not embeddings or not portfolio_item_ids:
            return []

        queries_cte = values(
            literal_column("embedding", Vector),
            name="queries"
        ).data([(e,) for e in embeddings]).cte()

        qna_alias = aliased(QnA)
        query = select(qna_alias).where(
            qna_alias.status == QnAStatus.CONFIRMED
        )

        if portfolio_item_ids:
            query = query.where(
                qna_alias.portfolio_item_id.in_(portfolio_item_ids)
            )

        lateral_sq = query.order_by(
            qna_alias.question_embedding.cosine_distance(queries_cte.c.embedding)
        ).limit(3).lateral("qnas")
        
        stmt = select(lateral_sq).join(queries_cte, literal_column("true"))
        results = await self.db.execute(stmt)
        
        unique_qnas = {qna.id: qna for qna in results.scalars().all()}
        return list(unique_qnas.values())
        