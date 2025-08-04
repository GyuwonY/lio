from typing import List
from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate


class PortfolioCRUD:
    async def get_portfolios_by_user(
        self, db: AsyncSession, *, user_id: int
    ) -> List[Portfolio]:
        result = await db.execute(select(Portfolio).filter(Portfolio.user_id == user_id))
        return list(result.scalars().all())

    async def create_portfolio(
        self, db: AsyncSession, *, portfolio_in: PortfolioCreate, user_id: int
    ) -> Portfolio:
        db_portfolio = Portfolio(**portfolio_in.model_dump(), user_id=user_id)
        db.add(db_portfolio)
        await db.commit()
        await db.refresh(db_portfolio)
        return db_portfolio
