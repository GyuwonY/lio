from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.portfolio import Portfolio, PortfolioSourceType, PortfolioStatus
from app.models.portfolio_item import PortfolioItem, PortfolioItemStatus


class PortfolioCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db


    async def get_portfolios_by_user(self, *, user_id: int) -> List[Portfolio]:
        result = await self.db.execute(
            select(Portfolio)
            .where(
                Portfolio.user_id == user_id,
                Portfolio.status != PortfolioStatus.DELETED,
            )
        )
        return list(result.scalars().unique().all())


    async def get_portfolio_by_id_without_item(self, *, portfolio_id: int, user_id: int) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio)
            .where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id
            )
        )
        return result.scalars().first()
    
    
    async def get_confirmed_portfolio_by_id(
        self, *, portfolio_id: int, user_id: int
    ) -> Portfolio | None:
        """ID와 사용자 ID로 특정 포트폴리오를 조회합니다 (items 포함)."""
        result = await self.db.execute(
            select(Portfolio)
            .options(
                selectinload(Portfolio.items.and_(PortfolioItem.status == PortfolioItemStatus.CONFIRMED))
            )
            .where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.status == PortfolioStatus.CONFIRMED,
            )
        )
        return result.scalars().first()
    

    async def get_portfolio_by_id(
        self, *, portfolio_id: int, user_id: int
    ) -> Portfolio | None:
        """ID와 사용자 ID로 특정 포트폴리오를 조회합니다 (items 포함)."""
        result = await self.db.execute(
            select(Portfolio)
            .options(
                selectinload(Portfolio.items.and_(PortfolioItem.status != PortfolioItemStatus.DELETED))
            )
            .where(
                Portfolio.id == portfolio_id,
                Portfolio.user_id == user_id,
                Portfolio.status != PortfolioStatus.DELETED,
            )
        )
        return result.scalars().first()


    async def create_portfolio(
        self,
        *,
        user_id: int,
        source_type: PortfolioSourceType,
        source_url: str | None,
        status: PortfolioStatus,
        items: List[PortfolioItem],
    ) -> Portfolio:
        """
        Portfolio와 그에 속한 Item들을 생성합니다.
        """
        db_portfolio = Portfolio(
            user_id=user_id,
            source_type=source_type,
            source_url=source_url,
            status=status,
            items=items,
        )

        self.db.add(db_portfolio)
        await self.db.flush()
        await self.db.refresh(db_portfolio)

        refreshed_portfolio = await self.get_portfolio_by_id(
            portfolio_id=db_portfolio.id, user_id=user_id
        )
        return refreshed_portfolio


    async def delete_portfolio(self, *, portfolio_id: int, user_id: int) -> bool:
        db_portfolio = await self.get_portfolio_by_id(
            portfolio_id=portfolio_id, user_id=user_id
        )
        if not db_portfolio:
            return False

        db_portfolio.status = PortfolioStatus.DELETED

        for item in db_portfolio.items:
            item.status = PortfolioItemStatus.DELETED

        await self.db.flush()
        return True
