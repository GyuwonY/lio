from typing import List
import uuid
from fastapi import Depends, HTTPException, status

from app.crud.portfolio_crud import PortfolioCRUD
from app.crud.portfolio_item_crud import PortfolioItemCRUD
from app.models.portfolio_item import PortfolioItemStatus
from app.schemas.portfolio_item_schema import (
    PortfolioItemRead,
    PortfolioItemsCreate,
    PortfolioItemsUpdate,
)
from app.models.user import User
from app.services.rag_service import RAGService


class PortfolioItemService:
    def __init__(
        self,
        portfolio_crud: PortfolioCRUD = Depends(),
        crud: PortfolioItemCRUD = Depends(),
        rag_service: RAGService = Depends(),
    ):
        self.portfolio_crud = portfolio_crud
        self.crud = crud
        self.rag_service = rag_service

    async def create_portfolio_items(
        self, *, portfolio_items_create: PortfolioItemsCreate, current_user: User
    ) -> List[PortfolioItemRead]:
        portfolio = await self.portfolio_crud.get_portfolio_by_id_without_items(
            portfolio_id=portfolio_items_create.portfolio_id, user_id=current_user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        created_items = await self.crud.create_portfolio_items(
            portfolio_items_create=portfolio_items_create
        )
        return [PortfolioItemRead.model_validate(item) for item in created_items]

    async def get_portfolio_items_by_portfolio_id(
        self, *, portfolio_id: uuid.UUID, current_user: User
    ) -> List[PortfolioItemRead]:
        portfolio_items = await self.crud.get_portfolio_items_by_portfolio_id(
            portfolio_id=portfolio_id
        )
        return [PortfolioItemRead.model_validate(item) for item in portfolio_items]

    async def update_portfolio_items(
        self, *, items_in: PortfolioItemsUpdate, current_user: User
    ) -> List[PortfolioItemRead]:
        item_ids = [item.id for item in items_in.items]
        portfolio_items = await self.crud.get_portfolio_item_by_ids(
            portfolio_item_ids=item_ids
        )
        item_update_dict = {item.id: item for item in items_in.items}

        for item in portfolio_items:
            item_update = item_update_dict[item.id]

            item.content = item_update.content
            item.start_date = (
                item_update.start_date if item_update.start_date else item.start_date
            )
            item.end_date = (
                item_update.end_date if item_update.end_date else item.end_date
            )
            item.topic = item_update.topic
            item.type = item_update.type
            item.tech_stack = item_update.tech_stack

        return [
            PortfolioItemRead(
                type=portfolio_item.type,
                topic=portfolio_item.topic,
                start_date=portfolio_item.start_date,
                end_date=portfolio_item.end_date,
                content=portfolio_item.content,
                tech_stack=portfolio_item.tech_stack,
                id=portfolio_item.id,
                portfolio_id=portfolio_item.portfolio_id,
                created_at=portfolio_item.created_at,
            )
            for portfolio_item in portfolio_items
        ]

    async def delete_portfolio_items(
        self, *, portfolio_item_ids: List[uuid.UUID], current_user: User
    ) -> None:
        # TODO: Check ownership of portfolio items
        deleted = await self.crud.delete_portfolio_items(
            portfolio_item_ids=portfolio_item_ids
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        return None
