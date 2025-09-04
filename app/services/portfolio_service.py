import uuid
from typing import List
from fastapi import Depends, HTTPException, status

from app.crud.portfolio_crud import PortfolioCRUD
from app.crud.user_crud import UserCRUD
from app.models.portfolio_item import PortfolioItem, PortfolioItemStatus
from app.schemas.portfolio_item_schema import PortfolioItemRead, PortfolioItemsUpdate
from app.schemas.portfolio_schema import (
    PortfolioCreateFromText,
    PortfolioCreateWithPdf,
    PortfolioConfirm,
    PortfolioRead,
    PortfolioUpdate,
)
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioSourceType, PortfolioStatus
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService


class PortfolioService:
    def __init__(
        self,
        crud: PortfolioCRUD = Depends(),
        user_crud: UserCRUD = Depends(),
        rag_service: RAGService = Depends(),
        llm_service: LLMService = Depends(),
    ):
        self.crud = crud
        self.user_crud = user_crud
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

            structured_items = await self.llm_service.structure_portfolio_from_text(
                text=text
            )
            
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
    ) -> PortfolioRead:
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

        return PortfolioRead(
            id=portfolio.id,
            user_id=portfolio.user_id,
            status=portfolio.status,
            name=portfolio.name,
            source_type=portfolio.source_type.value,
            source_url=portfolio.source_url,
            created_at=portfolio.created_at,
            items=[PortfolioItemRead(
                id=portfolio_item.id,
                portfolio_id=portfolio_item.portfolio_id,
                created_at=portfolio_item.created_at,
                type=portfolio_item.type,
                topic=portfolio_item.topic,
                start_date=portfolio_item.start_date,
                end_date=portfolio_item.end_date,
                content=portfolio_item.content,
                tech_stack=portfolio_item.tech_stack,
            ) for portfolio_item in portfolio.items]
        )


    async def get_portfolios_by_user(self, *, current_user: User) -> List[PortfolioRead]:
        portfolios = await self.crud.get_portfolios_by_user(user_id=current_user.id)
        return [PortfolioRead(
            id=portfolio.id,
            user_id=portfolio.user_id,
            status=portfolio.status,
            name=portfolio.name,
            source_type=portfolio.source_type.value,
            source_url=portfolio.source_url,
            created_at=portfolio.created_at,
        ) for portfolio in portfolios]


    async def get_portfolio_by_id(self, *, portfolio_id: uuid.UUID, current_user: User) -> Portfolio:
        """ID로 특정 포트폴리오를 조회합니다."""
        portfolio = await self.crud.get_portfolio_by_id(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 해당 포트폴리오에 접근할 권한이 없습니다.",
            )
        return portfolio


    async def get_portfolio_by_email_and_id(
        self, *, email: str, portfolio_id: uuid.UUID
    ) -> Portfolio:
        """이메일과 ID로 특정 포트폴리오를 조회합니다."""
        user = await self.user_crud.get_user_by_email(email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{email} 사용자를 찾을 수 없습니다.",
            )

        portfolio = await self.crud.get_confirmed_portfolio_by_id(
            portfolio_id=portfolio_id, user_id=user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 해당 포트폴리오에 접근할 권한이 없습니다.",
            )
        return portfolio
    
    
    async def get_user_portfolios(self, *, current_user: User) -> List[Portfolio]:
        return await self.crud.get_portfolios_by_user(user_id=current_user.id)


    async def delete_portfolio(self, *, portfolio_id: uuid.UUID, current_user: User) -> None:
        deleted = await self.crud.delete_portfolio(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        return None


    async def update_portfolio(self, *, portfolio_id: uuid.UUID, portfolio_update: PortfolioUpdate, current_user: User) -> PortfolioRead:
        portfolio = await self.crud.get_portfolio_by_id_without_item(
            portfolio_id=portfolio_id,
            user_id=current_user.id
        )
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 해당 포트폴리오에 접근할 권한이 없습니다.",
            )
        
        portfolio.name = portfolio_update.name
        return PortfolioRead(
            id=portfolio.id,
            user_id=portfolio.user_id,
            status=portfolio.status,
            name=portfolio.name,
            source_type=portfolio.source_type.value,
            source_url=portfolio.source_url,
            created_at=portfolio.created_at,
        )
    