import uuid
from typing import List
from fastapi import Depends
from sqlalchemy import cast, desc, literal_column, values
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, aliased
from pgvector.sqlalchemy import Vector

from app.db.session import get_db
from app.models.portfolio import Portfolio, PortfolioSourceType, PortfolioStatus
from app.models.portfolio_item import (
    PortfolioItem,
    PortfolioItemStatus,
)


class PortfolioCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_portfolios_by_user_without_items(
        self, *, user_id: uuid.UUID
    ) -> List[Portfolio]:
        result = await self.db.execute(
            select(Portfolio).where(
                Portfolio.user_id == user_id,
                Portfolio.status != PortfolioStatus.DELETED,
            ).order_by(desc(Portfolio.created_at))
        )
        return list(result.scalars().unique().all())

    async def get_portfolio_by_id_without_items(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio).where(
                Portfolio.id == portfolio_id, Portfolio.user_id == user_id
            )
        )
        return result.scalars().first()

    async def get_published_portfolio_by_id_without_items(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio).where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.status == PortfolioStatus.PUBLISHED,
            )
        )
        return result.scalars().first()

    async def get_draft_qna_portfolio_by_id_with_items(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio)
            .options(
                selectinload(
                    Portfolio.items.and_(
                        PortfolioItem.status == PortfolioItemStatus.CONFIRMED
                    )
                )
            )
            .where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.status == PortfolioStatus.DRAFT_QNA,
            )
        )
        return result.scalars().first()

    async def get_published_portfolio_by_id_with_items(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio)
            .options(
                selectinload(
                    Portfolio.items.and_(
                        PortfolioItem.status == PortfolioItemStatus.CONFIRMED
                    )
                )
            )
            .where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.status == PortfolioStatus.PUBLISHED,
            )
        )
        return result.scalars().first()

    async def get_portfolio_by_id_with_items(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio)
            .options(
                selectinload(
                    Portfolio.items.and_(
                        PortfolioItem.status != PortfolioItemStatus.DELETED
                    )
                )
            )
            .where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.status != PortfolioStatus.DELETED,
            )
        )
        return result.scalars().first()

    async def get_portfolio_item_by_ids(
        self, *, portfolio_item_ids: List[uuid.UUID]
    ) -> List[PortfolioItem]:
        result = await self.db.execute(
            select(PortfolioItem).where(
                PortfolioItem.id.in_(portfolio_item_ids),
                PortfolioItem.status != PortfolioItemStatus.DELETED,
            )
        )
        return list(result.scalars().all())

    async def create_portfolio(
        self,
        *,
        user_id: uuid.UUID,
        source_type: PortfolioSourceType,
        source_url: str | None,
        status: PortfolioStatus,
        items: List[PortfolioItem],
        name: str | None,
    ) -> Portfolio:
        db_portfolio = Portfolio(
            user_id=user_id,
            source_type=source_type,
            source_url=source_url,
            status=status,
            items=items,
            name=name,
        )

        self.db.add(db_portfolio)
        await self.db.flush()
        await self.db.refresh(db_portfolio)

        refreshed_portfolio = await self.get_portfolio_by_id_with_items(
            portfolio_id=db_portfolio.id, user_id=user_id
        )
        return refreshed_portfolio

    async def delete_portfolio(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        db_portfolio = await self.get_portfolio_by_id_with_items(
            portfolio_id=portfolio_id, user_id=user_id
        )
        if not db_portfolio:
            return False

        db_portfolio.status = PortfolioStatus.DELETED

        for item in db_portfolio.items:
            item.status = PortfolioItemStatus.DELETED

        await self.db.flush()
        return True

    async def delete_portfolio_items(
        self, *, portfolio_item_ids: List[uuid.UUID]
    ) -> bool:
        db_portfolio_items = await self.get_portfolio_item_by_ids(
            portfolio_item_ids=portfolio_item_ids
        )
        if not db_portfolio_items:
            return False

        for item in db_portfolio_items:
            item.status = PortfolioItemStatus.DELETED

        await self.db.flush()
        return True

    async def search_portfolio_items_by_embedding(
        self,
        *,
        embeddings: List[List[float]],
        portfolio_id: uuid.UUID,
        limit: int = 5,
    ) -> List[PortfolioItem]:
        queries_cte = (
            values(literal_column("embedding", Vector), name="queries")
            .data([(e,) for e in embeddings])
            .cte()
        )

        items_alias = aliased(PortfolioItem)
        lateral_sq = (
            select(items_alias)
            .where(
                items_alias.portfolio_id == portfolio_id,
                items_alias.status == PortfolioItemStatus.CONFIRMED,
            )
            .order_by(
                items_alias.embedding.l2_distance(
                    cast(queries_cte.c.embedding, Vector)
                )
            )
            .limit(limit)
            .lateral()
        )

        items_from_lateral = aliased(PortfolioItem, lateral_sq)
        stmt = (
            select(items_from_lateral)
            .select_from(queries_cte)
            .join(items_from_lateral, literal_column("true"))
        )
        results = await self.db.execute(stmt)
        return list(results.scalars().unique().all())
