from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.encoders import jsonable_encoder
from fastapi import Depends

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate
from app.db.session import get_db


class PortfolioCRUD:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db

    async def get_portfolios_by_user(self, *, user_id: int) -> List[Portfolio]:
        result = await self.db.execute(
            select(Portfolio).filter(Portfolio.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_portfolio_by_id(self, *, portfolio_id: int) -> Portfolio | None:
        result = await self.db.execute(
            select(Portfolio).filter(Portfolio.id == portfolio_id)
        )
        return result.scalars().first()

    async def create_portfolio(
        self, *, portfolio_in: PortfolioCreate, user_id: int
    ) -> Portfolio:
        db_portfolio = Portfolio(**portfolio_in.model_dump(), user_id=user_id)
        self.db.add(db_portfolio)
        await self.db.commit()
        await self.db.refresh(db_portfolio)
        return db_portfolio

    async def update_portfolio(
        self, *, db_obj: Portfolio, obj_in: PortfolioUpdate | dict[str, Any]
    ) -> Portfolio:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
