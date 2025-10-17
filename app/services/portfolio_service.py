import uuid
from typing import List
from fastapi import Depends, HTTPException, status
from app.crud.portfolio_crud import PortfolioCRUD
from app.crud.user_crud import UserCRUD
from app.db.session import AsyncSessionLocal
from app.models.portfolio_item import PortfolioItem, PortfolioItemStatus
from app.schemas.portfolio_item_schema import PortfolioItemRead
from app.schemas.portfolio_schema import (
    PortfolioCreateFromText,
    PortfolioCreateWithPdf,
    PortfolioRead,
    PortfolioReadWithoutItems,
    PortfolioUpdate,
    PublishedPortfolioRead,
)
from app.models.user import User
from app.models.portfolio import PortfolioSourceType, PortfolioStatus
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.fcm_service import FCMService


class PortfolioService:
    def __init__(
        self,
        crud: PortfolioCRUD = Depends(),
        user_crud: UserCRUD = Depends(),
        rag_service: RAGService = Depends(),
        llm_service: LLMService = Depends(),
        fcm_service: FCMService = Depends(),
    ):
        self.crud = crud
        self.user_crud = user_crud
        self.rag_service = rag_service
        self.llm_service = llm_service
        self.fcm_service = fcm_service

    async def create_portfolio_from_text(
        self, *, portfolio_in: PortfolioCreateFromText, current_user: User
    ) -> PortfolioRead:
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
            name=portfolio_in.name,
            theme=portfolio_in.theme,
        )

        return PortfolioRead.model_validate(created_portfolio)

    async def create_draft_portfolio(
        self, *, portfolio_in: PortfolioCreateWithPdf, current_user: User
    ) -> PortfolioRead:
        """DRAFT 상태의 포트폴리오를 생성합니다."""
        draft_portfolio = await self.crud.create_portfolio(
            user_id=current_user.id,
            source_type=PortfolioSourceType.PDF,
            source_url=portfolio_in.file_path,
            status=PortfolioStatus.DRAFT,
            items=[],
            name=portfolio_in.name,
            theme=portfolio_in.theme,
        )
        return PortfolioRead.model_validate(draft_portfolio)

    async def create_portfolio_from_pdf_background(
        self, *, portfolio_id: uuid.UUID, user_id: uuid.UUID, file_path: str
    ):
        async with AsyncSessionLocal() as db:
            portfolio = None
            user = None
            try:
                portfolio_crud = PortfolioCRUD(db)
                user_crud = UserCRUD(db)

                portfolio = await portfolio_crud.get_portfolio_by_id_with_items(
                    portfolio_id=portfolio_id, user_id=user_id
                )
                if not portfolio:
                    print(
                        f"Error: Portfolio not found for background processing: {portfolio_id}"
                    )
                    return

                user = await user_crud.get_user_by_id(user_id=user_id)

                text = await self.rag_service.extract_text_from_gcs_pdf(
                    gcs_url=file_path
                )
                if not text.strip():
                    raise ValueError("PDF 파일에서 텍스트를 추출할 수 없습니다.")

                structured_items = await self.llm_service.structure_portfolio_from_text(
                    text=text
                )
                if not structured_items or not structured_items.items:
                    raise ValueError("LLM이 텍스트를 구조화하지 못했습니다.")

                created_items = [
                    PortfolioItem(
                        type=item.type,
                        topic=item.topic,
                        start_date=item.start_date,
                        end_date=item.end_date,
                        content=item.content,
                        tech_stack=item.tech_stack,
                        portfolio_id=portfolio_id,
                        status=PortfolioItemStatus.PENDING,
                    )
                    for item in structured_items.items
                ]

                portfolio.items.extend(created_items)
                portfolio.status = PortfolioStatus.PENDING

                if user and user.fcm_token:
                    self.fcm_service.send_notification(
                        token=user.fcm_token,
                        title="create_portfolio_success",
                        body=f"{portfolio_id}",
                    )

            except Exception as e:
                print(f"Error processing portfolio {portfolio_id}: {e}")
                if portfolio:
                    portfolio.status = PortfolioStatus.FAILED

                if user and user.fcm_token:
                    self.fcm_service.send_notification(
                        token=user.fcm_token,
                        title="create_portfolio_fail",
                        body=f"{portfolio_id}",
                    )
            finally:
                if portfolio:
                    db.add(portfolio)
                    await db.commit()

    async def confirm_portfolio(
        self, *, portfolio_id: uuid.UUID, current_user: User
    ) -> PortfolioRead:
        portfolio = await self.crud.get_portfolio_by_id_with_items(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없습니다.",
            )

        if portfolio.status != PortfolioStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 확정되었거나 처리 중인 포트폴리오입니다.",
            )

        portfolio.status = PortfolioStatus.CONFIRMED
        embeddings = await self.rag_service.embed_portfolio_items(items=portfolio.items)

        for item, embedding in zip(portfolio.items, embeddings):
            item.embedding = embedding
            item.status = PortfolioItemStatus.CONFIRMED

        return PortfolioRead.model_validate(portfolio)

    async def publish_portfolio(
        self, *, portfolio_id: uuid.UUID, current_user: User
    ) -> PortfolioReadWithoutItems:
        published_portfolio = (
            await self.crud.get_published_portfolio_by_id_without_items(
                portfolio_id=portfolio_id, user_id=current_user.id
            )
        )

        portfolio = await self.crud.get_portfolio_by_id_without_items(
            portfolio_id=portfolio_id, user_id=current_user.id
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="존재하지 않는 포트폴리오입니다.",
            )

        if portfolio.status != PortfolioStatus.PENDING_QNA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="확정되지 않은 포트폴리오입니다.",
            )

        if published_portfolio:
            published_portfolio.status = PortfolioStatus.PENDING_QNA

        portfolio.status = PortfolioStatus.PUBLISHED

        return PortfolioReadWithoutItems.model_validate(portfolio)

    async def get_portfolios_by_user(
        self, *, current_user: User
    ) -> List[PortfolioReadWithoutItems]:
        portfolios = await self.crud.get_portfolios_by_user_without_items(
            user_id=current_user.id
        )
        return [PortfolioReadWithoutItems.model_validate(p) for p in portfolios]

    async def get_portfolio_by_id(
        self, *, portfolio_id: uuid.UUID, current_user: User
    ) -> PortfolioRead:
        """ID로 특정 포트폴리오를 조회합니다."""
        portfolio = await self.crud.get_portfolio_by_id_with_items(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 해당 포트폴리오에 접근할 권한이 없습니다.",
            )
        return PortfolioRead.model_validate(portfolio)

    async def get_published_portfolio_by_nickname(
        self, *, nickname: str
    ) -> PublishedPortfolioRead:
        user = await self.user_crud.get_user_by_nickname(nickname=nickname)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{nickname} 사용자를 찾을 수 없습니다.",
            )

        portfolio = await self.crud.get_published_portfolio_by_user_id_with_items(
            user_id=user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 해당 포트폴리오에 접근할 권한이 없습니다.",
            )
        return PublishedPortfolioRead(
            id=portfolio.id,
            user_id=user.id,
            status=portfolio.status,
            name=portfolio.name,
            created_at=portfolio.created_at,
            items=[PortfolioItemRead.model_validate(item) for item in portfolio.items],
            first_name=user.first_name,
            last_name=user.last_name,
            address=user.address,
            job=user.job,
            theme=portfolio.theme
        )

    async def delete_portfolio(
        self, *, portfolio_id: uuid.UUID, current_user: User
    ) -> None:
        deleted = await self.crud.delete_portfolio(
            portfolio_id=portfolio_id, user_id=current_user.id
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        return None

    async def update_portfolio(
        self,
        *,
        portfolio_id: uuid.UUID,
        portfolio_update: PortfolioUpdate,
        current_user: User,
    ) -> PortfolioReadWithoutItems:
        portfolio = await self.crud.get_portfolio_by_id_without_items(
            portfolio_id=portfolio_id, user_id=current_user.id
        )

        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 해당 포트폴리오에 접근할 권한이 없습니다.",
            )

        portfolio.name = portfolio_update.name
        return PortfolioReadWithoutItems.model_validate(portfolio)
    
    async def get_published_portfolios(self) -> List[PortfolioReadWithoutItems]:
        portfolios = await self.crud.get_published_portfolios()
        return [PortfolioReadWithoutItems.model_validate(p) for p in portfolios]
        
