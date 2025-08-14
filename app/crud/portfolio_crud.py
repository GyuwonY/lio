from typing import List, Any, Dict
from fastapi import Depends, HTTPException, status
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
        """사용자의 모든 포트폴리오 목록을 조회합니다 (items 포함)."""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.items))
            .where(Portfolio.user_id == user_id, Portfolio.status != PortfolioStatus.DELETED)
        )
        return list(result.scalars().unique().all())


    async def get_portfolio_by_id(self, *, portfolio_id: int, user_id: int) -> Portfolio | None:
        """ID와 사용자 ID로 특정 포트폴리오를 조회합니다 (items 포함)."""
        result = await self.db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.items))
            .where(Portfolio.id == portfolio_id, Portfolio.user_id == user_id, Portfolio.status != PortfolioStatus.DELETED)
        )
        return result.scalars().first()
    
    
    async def get_portfolio_item_by_ids(self, *, portfolio_item_ids: List[int]) -> List[PortfolioItem]:
        result = await self.db.execute(
            select(PortfolioItem)
            .where(PortfolioItem.id.in_(portfolio_item_ids))
        )
        return list(result.scalars().all())
        

    async def create_portfolio(
        self, *, user_id: int, source_type: PortfolioSourceType, source_url: str | None, status: PortfolioStatus, items_data: List[dict]
    ) -> Portfolio:
        """
        Portfolio와 그에 속한 Item들을 생성합니다.
        """
        db_portfolio = Portfolio(
            user_id=user_id,
            source_type=source_type,
            source_identifier=source_url,
            status=status
        )
        
        for item_data in items_data:
            db_item = PortfolioItem(**item_data)
            db_portfolio.items.append(db_item)

        self.db.add(db_portfolio)
        await self.db.commit()
        await self.db.refresh(db_portfolio)
        
        refreshed_portfolio = await self.get_portfolio_by_id(portfolio_id=db_portfolio.id, user_id=user_id)
        return refreshed_portfolio


    async def update_portfolio_status_and_items(
        self, *, portfolio_id: int, user_id: int, embeddings: List[List[float]]
    ) -> Portfolio:
        """포트폴리오의 상태를 CONFIRMED로 변경하고, 각 항목에 임베딩을 추가합니다."""
        portfolio = await self.get_portfolio_by_id(portfolio_id=portfolio_id, user_id=user_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="포트폴리오를 찾을 수 없습니다.")
        
        if len(portfolio.items) != len(embeddings):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="항목의 수와 임베딩의 수가 일치하지 않습니다.")

        portfolio.status = PortfolioStatus.CONFIRMED
        
        for item, embedding in zip(portfolio.items, embeddings):
            item.embedding = embedding
            
        await self.db.commit()
        await self.db.refresh(portfolio)
        return portfolio


    async def update_portfolio_items(
        self, *, items_update_data: List[Dict[str, Any]], user_id: int
    ) -> Portfolio:
        """여러 포트폴리오 항목을 업데이트합니다."""
        if not items_update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="수정할 항목이 없습니다.")

        first_item_id = items_update_data[0]['id']
        
        stmt = select(PortfolioItem).where(PortfolioItem.id == first_item_id)
        result = await self.db.execute(stmt)
        first_db_item = result.scalars().first()

        if not first_db_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID {first_item_id}에 해당하는 항목을 찾을 수 없습니다.")
        
        portfolio_id = first_db_item.portfolio_id
        
        portfolio = await self.get_portfolio_by_id(portfolio_id=portfolio_id, user_id=user_id)
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="포트폴리오에 접근할 권한이 없습니다.")

        for item_data in items_update_data:
            item_id = item_data.pop("id")
            
            db_item = await self.db.get(PortfolioItem, item_id)
            if not db_item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"ID {item_id}에 해당하는 항목을 찾을 수 없습니다.")

            if db_item.portfolio_id != portfolio_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="모든 항목은 동일한 포트폴리오에 속해야 합니다.")

            for key, value in item_data.items():
                if value is not None:
                    setattr(db_item, key, value)
        
        await self.db.commit()
        
        updated_portfolio = await self.get_portfolio_by_id(portfolio_id=portfolio_id, user_id=user_id)
        return updated_portfolio


    async def delete_portfolio(self, *, portfolio_id: int, user_id: int) -> bool:
        db_portfolio = await self.get_portfolio_by_id(portfolio_id=portfolio_id, user_id=user_id)
        if not db_portfolio:
            return False
        
        db_portfolio.status = PortfolioStatus.DELETED
        
        for item in db_portfolio.items:
            item.status = PortfolioItemStatus.DELETED
        
        await self.db.commit()
        return True
    
    
    async def delete_portfolio_items(self, *, portfolio_item_ids: List[int]) -> bool:
        db_portfolio_items = await self.get_portfolio_item_by_ids(portfolio_item_ids=portfolio_item_ids)
        if not db_portfolio_items:
            return False
        
        for item in db_portfolio_items:
            item.status = PortfolioItemStatus.DELETED
        
        await self.db.commit()
        return True
