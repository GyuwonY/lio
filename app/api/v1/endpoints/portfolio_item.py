from typing import List
import uuid
from fastapi import APIRouter, Depends

from app.schemas.portfolio_item_schema import (
    PortfolioItemRead,
    PortfolioItemsCreate,
    PortfolioItemsUpdate,
    PortfolioItemDelete,
)
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.portfolio_item_service import PortfolioItemService

router = APIRouter()


@router.post("/", response_model=List[PortfolioItemRead])
async def create_portfolio_items(
    current_user: User = Depends(get_current_user),
    service: PortfolioItemService = Depends(),
    *,
    portfolio_items_create: PortfolioItemsCreate,
) -> List[PortfolioItemRead]:
    return await service.create_portfolio_items(
        portfolio_items_create=portfolio_items_create, current_user=current_user
    )


@router.get("/by-portfolio/{portfolio_id}", response_model=List[PortfolioItemRead])
async def get_portfolio_items_by_portfolio_id(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: PortfolioItemService = Depends(),
) -> List[PortfolioItemRead]:
    """
    포트폴리오 ID로 포트폴리오 항목 목록을 조회합니다.
    """
    return await service.get_portfolio_items_by_portfolio_id(
        portfolio_id=portfolio_id, current_user=current_user
    )


@router.put("/", response_model=List[PortfolioItemRead])
async def update_portfolio_items(
    current_user: User = Depends(get_current_user),
    service: PortfolioItemService = Depends(),
    *,
    items_in: PortfolioItemsUpdate,
) -> List[PortfolioItemRead]:
    """
    포트폴리오의 여러 항목을 업데이트합니다.
    """
    updated_portfolio = await service.update_portfolio_items(
        items_in=items_in, current_user=current_user
    )
    return updated_portfolio


@router.delete("/")
async def delete_portfolio_items(
    current_user: User = Depends(get_current_user),
    service: PortfolioItemService = Depends(),
    *,
    portfolio_delete: PortfolioItemDelete,
):
    """
    ID로 특정 포트폴리오 item 삭제합니다.
    """
    return await service.delete_portfolio_items(
        portfolio_item_ids=portfolio_delete.portfolio_item_ids,
        current_user=current_user,
    )
