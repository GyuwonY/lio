from typing import List
from fastapi import Depends, HTTPException, status

from app.crud.portfolio_crud import PortfolioCRUD
from app.models.portfolio_item import PortfolioItem, PortfolioItemStatus
from app.schemas.llm_schema import LLMPortfolio
from app.schemas.portfolio_schema import (
    PortfolioCreateFromText,
    PortfolioCreateWithPdf,
    PortfolioItemsUpdate,
    PortfolioConfirm,
)
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioSourceType, PortfolioStatus
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService


class PortfolioService:
    def __init__(
        self,
        crud: PortfolioCRUD = Depends(),
        rag_service: RAGService = Depends(),
        llm_service: LLMService = Depends(),
    ):
        self.crud = crud
        self.rag_service = rag_service
        self.llm_service = llm_service

    async def create_portfolio_from_text(
        self, *, portfolio_in: PortfolioCreateFromText, current_user: User
    ) -> Portfolio:
        if not portfolio_in.text_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="포트폴리오로 생성할 데이터가 없습니다.",
            )

        items = [
            PortfolioItem(
                type=item.type,
                status=PortfolioItemStatus.CONFIRMED,
                topic=item.topic,
                start_date=item.start_date,
                end_date=item.end_date,
                content=item.content,
                tech_stack=item.tech_stack,
            )
            for item in portfolio_in.text_items
        ]

        embeddings = await self.rag_service.embed_portfolio_items(items=items)

        for i, item in enumerate(items):
            item.embedding = embeddings[i]

        created_portfolio = await self.crud.create_portfolio(
            user_id=current_user.id,
            source_type=PortfolioSourceType.TEXT,
            source_url=None,
            status=PortfolioStatus.CONFIRMED,
            items=items,
        )

        return created_portfolio

    async def create_portfolio_from_pdf(
        self, *, portfolio_in: PortfolioCreateWithPdf, current_user: User
    ) -> Portfolio:
        try:
            text = await self.rag_service.extract_text_from_gcs_pdf(
                gcs_url=portfolio_in.file_path
            )
            if not text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF 파일에서 텍스트를 추출할 수 없습니다.",
                )

            llm_output_str = await self.llm_service.structure_portfolio_from_text(
                text=text
            )
            structured_items = LLMPortfolio.model_validate_json(llm_output_str)
            
            if not structured_items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LLM이 텍스트를 구조화하지 못했습니다.",
                )

            items = [
                PortfolioItem(
                    type=item.type,
                    status=PortfolioItemStatus.PENDING,
                    topic=item.topic,
                    start_date=item.start_date,
                    end_date=item.end_date,
                    content=item.content,
                    tech_stack=item.tech_stack,
                )
                for item in structured_items.items
            ]

            created_portfolio = await self.crud.create_portfolio(
                user_id=current_user.id,
                source_type=PortfolioSourceType.PDF,
                source_url=portfolio_in.file_path,
                status=PortfolioStatus.PENDING,
                items=items,
            )
            return created_portfolio

        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GCS에서 파일을 찾을 수 없습니다: {portfolio_in.file_path}",
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF 처리 또는 LLM 응답 파싱 중 오류 발생: {e}",
            )

    async def confirm_portfolio(
        self, *, confirm_in: PortfolioConfirm, current_user: User
    ) -> Portfolio:
        portfolio = await self.crud.get_portfolio_by_id(
            portfolio_id=confirm_in.portfolio_id, user_id=current_user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없습니다.",
            )

        if portfolio.status != PortfolioStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 확정된 포트폴리오입니다.",
            )

        portfolio.status = PortfolioStatus.CONFIRMED
        embeddings = await self.rag_service.embed_portfolio_items(items=portfolio.items)

        for item, embedding in zip(portfolio.items, embeddings):
            item.embedding = embedding
            item.status = PortfolioItemStatus.CONFIRMED

        return portfolio

    async def get_user_portfolios(self, *, current_user: User) -> List[Portfolio]:
        return await self.crud.get_portfolios_by_user(user_id=current_user.id)

    async def update_portfolio_items(
        self, *, items_in: PortfolioItemsUpdate, current_user: User
    ) -> List[PortfolioItem]:
        item_ids = [item.id for item in items_in.items]
        portfolio_items = await self.crud.get_portfolio_item_by_ids(
            portfolio_item_ids=item_ids
        )
        item_update_dict = {item.id: item for item in items_in.items}

        items_to_re_embed = []
        for item in portfolio_items:
            if (
                item.status == PortfolioItemStatus.CONFIRMED
                and item.content != item_update_dict[item.id].content
            ):
                items_to_re_embed.append(item)

        if items_to_re_embed:
            embeddings = await self.rag_service.embed_portfolio_items(
                items=items_to_re_embed
            )
            embedding_map = {
                item.id: emb for item, emb in zip(items_to_re_embed, embeddings)
            }
        else:
            embedding_map = {}

        for item in portfolio_items:
            item_update = item_update_dict[item.id]
            if embedding_map.get(item.id):
                item.embedding = embedding_map[item.id]

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

        return portfolio_items

    async def delete_portfolio(self, *, portfolio_id: int, current_user: User) -> None:
        deleted = await self.crud.delete_portfolio(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        return None

    async def delete_portfolio_items(
        self, *, portfolio_item_ids: List[int], current_user: User
    ) -> None:
        deleted = await self.crud.delete_portfolio_items(
            portfolio_item_ids=portfolio_item_ids
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        return None
