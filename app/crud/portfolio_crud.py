from typing import List, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.portfolio import Portfolio
from app.models.portfolio_item import PortfolioItem

class PortfolioCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_portfolios_by_user(self, *, user_id: int) -> List[Portfolio]:
        """사용자의 모든 포트폴리오 목록을 조회합니다 (items 포함)."""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.items))
            .filter(Portfolio.user_id == user_id)
        )
        return list(result.scalars().unique().all())

    async def get_portfolio_by_id(self, *, portfolio_id: int, user_id: int) -> Portfolio | None:
        """ID와 사용자 ID로 특정 포트폴리오를 조회합니다 (items 포함)."""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.items))
            .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
        )
        return result.scalars().first()

    async def create_portfolio_with_items(
        self, *, user_id: int, source_type: str, source_identifier: str | None, items_data: List[dict]
    ) -> Portfolio:
        """
        Portfolio 세션과 그에 속한 Item들을 한번에 생성합니다.
        Embedding 벡터도 함께 저장합니다.
        """
        # 1. Portfolio "세션" 객체 생성
        db_portfolio = Portfolio(
            user_id=user_id,
            source_type=source_type,
            source_identifier=source_identifier,
        )
        
        # 2. PortfolioItem 객체들 생성
        for item_data in items_data:
            db_item = PortfolioItem(**item_data)
            db_portfolio.items.append(db_item)

        self.db.add(db_portfolio)
        await self.db.commit()
        await self.db.refresh(db_portfolio)
        
        # 관계된 items들이 로드되도록 refresh 후 다시 조회
        refreshed_portfolio = await self.get_portfolio_by_id(portfolio_id=db_portfolio.id, user_id=user_id)
        return refreshed_portfolio

    async def delete_portfolio(self, *, portfolio_id: int, user_id: int) -> bool:
        """포트폴리오와 하위 항목들을 모두 삭제합니다."""
        db_portfolio = await self.get_portfolio_by_id(portfolio_id=portfolio_id, user_id=user_id)
        if not db_portfolio:
            return False
        
        await self.db.delete(db_portfolio)
        await self.db.commit()
        return True

    # 기존 update, get_multi_by_ids 등은 필요시 유사한 방식으로 수정/구현 가능