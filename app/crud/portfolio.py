from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.models.portfolio import Portfolio
from app.schemas.portfolio import PortfolioCreate

async def get_portfolios_by_owner(db: AsyncSession, *, owner_id: int) -> List[Portfolio]:
    """
    특정 사용자가 소유한 모든 포트폴리오를 비동기적으로 조회합니다.
    """
    result = await db.execute(
        select(Portfolio).filter(Portfolio.owner_id == owner_id)
    )
    return result.scalars().all()

async def create_portfolio(db: AsyncSession, *, portfolio_in: PortfolioCreate, owner_id: int) -> Portfolio:
    """
    새로운 포트폴리오 메타데이터를 데이터베이스에 비동기적으로 생성합니다.
    """
    db_portfolio = Portfolio(
        **portfolio_in.model_dump(),
        owner_id=owner_id
    )
    db.add(db_portfolio)
    await db.commit()
    await db.refresh(db_portfolio)
    return db_portfolio
