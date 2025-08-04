from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.portfolio import PortfolioRead
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.portfolio_service import PortfolioService
from app.core.dependencies import get_portfolio_service
from app.db.session import get_db

router = APIRouter()


@router.post("/", response_model=PortfolioRead, status_code=201)
async def create_portfolio(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.create_portfolio(db=db, file=file, current_user=current_user)


@router.get("/", response_model=List[PortfolioRead])
async def read_portfolios(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    return await service.get_user_portfolios(db=db, current_user=current_user)
