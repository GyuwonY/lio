from typing import List
import uuid
from fastapi import Depends
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.portfolio_item import (
    PortfolioItem,
    PortfolioItemStatus,
    PortfolioItemType,
)
from app.schemas.portfolio_item_schema import PortfolioItemsCreate


class PortfolioItemCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def create_portfolio_items(
        self, *, portfolio_items_create: PortfolioItemsCreate
    ) -> List[PortfolioItem]:
        portfolio_items_data = [
            item.model_dump() for item in portfolio_items_create.portfolio_items
        ]
        for item_data in portfolio_items_data:
            item_data["portfolio_id"] = portfolio_items_create.portfolio_id

        stmt = (
            insert(PortfolioItem).values(portfolio_items_data).returning(PortfolioItem)
        )
        result = await self.db.execute(stmt)
        created_items = result.scalars().all()
        return list(created_items)

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

    async def get_confirmed_portfolio_items_by_portfolio_id(
        self, *, portfolio_id: uuid.UUID
    ) -> List[PortfolioItem]:
        result = await self.db.execute(
            select(PortfolioItem).where(
                PortfolioItem.portfolio_id == portfolio_id,
                PortfolioItem.status == PortfolioItemStatus.CONFIRMED,
            )
        )
        return list(result.scalars().all())

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

    async def get_portfolio_items_by_portfolio_id(
        self, *, portfolio_id: uuid.UUID
    ) -> List[PortfolioItem]:
        result = await self.db.execute(
            select(PortfolioItem).where(
                PortfolioItem.portfolio_id == portfolio_id,
                PortfolioItem.status != PortfolioItemStatus.DELETED,
            )
        )
        return list(result.scalars().all())
