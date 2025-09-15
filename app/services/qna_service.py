import asyncio
import uuid
from typing import List
from fastapi import BackgroundTasks, Depends, HTTPException, status

from app.crud.portfolio_crud import PortfolioCRUD
from app.db.session import AsyncSessionLocal
from app.crud.portfolio_item_crud import PortfolioItemCRUD
from app.crud.qna_crud import QnACRUD
from app.models.portfolio import PortfolioStatus
from app.models.qna import QnA, QnAStatus
from app.schemas.portfolio_schema import PortfolioReadWithoutItems
from app.schemas.qna_schema import (
    QnARead,
    QnACreate,
    QnAsUpdate,
)
from app.models.user import User
from app.models.portfolio_item import PortfolioItem
from app.services.fcm_service import FCMService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService


class QnAService:
    def __init__(
        self,
        qna_crud: QnACRUD = Depends(),
        llm_service: LLMService = Depends(),
        rag_service: RAGService = Depends(),
        portfolio_item_crud: PortfolioItemCRUD = Depends(),
        portfolio_crud: PortfolioCRUD = Depends(),
        fcm_service: FCMService = Depends(),
    ):
        self.qna_crud = qna_crud
        self.portfolio_item_crud = portfolio_item_crud
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.portfolio_crud = portfolio_crud
        self.fcm_service = fcm_service

    async def _generate_qna_for_item(self, *, item: PortfolioItem) -> List[QnACreate]:
        try:
            parsed_output = await self.llm_service.generate_qna_for_portfolio_item(
                item=item
            )

            return [
                QnACreate(
                    question=qna_set.question,
                    answer=qna_set.answer,
                    portfolio_item_id=item.id,
                )
                for qna_set in parsed_output.qnas
            ]
        except Exception as e:
            print(f"Error generating QnA for portfolio_item_id {item.id}: {e}")
            return []

    async def generate_qna_for_all_portfolios_background(
        self,
        *,
        current_user: User,
        portfolio_id: uuid.UUID,
    ):
        async with AsyncSessionLocal() as db:
            try:
                portfolio_crud = PortfolioCRUD(db)
                qna_crud = QnACRUD(db)

                portfolio = (
                    await portfolio_crud.get_draft_qna_portfolio_by_id_with_items(
                        portfolio_id=portfolio_id, user_id=current_user.id
                    )
                )

                if not portfolio:
                    print(
                        f"No confirmed portfolio items found for portfolio_id: {portfolio_id}"
                    )
                    return

                tasks = [
                    self._generate_qna_for_item(item=item) for item in portfolio.items
                ]
                results = await asyncio.gather(*tasks)

                qnas_to_create = []
                for result in results:
                    qnas_to_create.extend(result)

                if qnas_to_create:
                    await qna_crud.bulk_create_qnas(
                        qna_list=qnas_to_create, user_id=current_user.id
                    )

                portfolio.status = PortfolioStatus.PENDING_QNA
                await db.commit()
                
                if current_user and current_user.fcm_token:
                    self.fcm_service.send_notification(
                        token=current_user.fcm_token,
                        title="create_qna_success",
                        body=f"{portfolio_id}",
                    )
            except Exception as e:
                await db.rollback()
                print(f"Error generating QnA for portfolio {portfolio_id}: {e}")
                if current_user and current_user.fcm_token:
                    self.fcm_service.send_notification(
                        token=current_user.fcm_token,
                        title="create_qna_fail",
                        body=f"{portfolio_id}",
                    )

    async def add_qna_generation_task(
        self,
        *,
        background_tasks: BackgroundTasks,
        current_user: User,
        portfolio_id: uuid.UUID,
    ) -> PortfolioReadWithoutItems:
        portfolio = await self.portfolio_crud.get_portfolio_by_id_without_items(
            portfolio_id=portfolio_id, user_id=current_user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="포트폴리오를 찾을 수 없거나 해당 포트폴리오에 접근할 권한이 없습니다.",
            )

        portfolio.status = PortfolioStatus.DRAFT_QNA

        background_tasks.add_task(
            self.generate_qna_for_all_portfolios_background,
            current_user=current_user,
            portfolio_id=portfolio_id,
        )
        return PortfolioReadWithoutItems.model_validate(portfolio)

    async def get_qnas_by_portfolio(
        self, *, portfolio_id: uuid.UUID, current_user: User
    ) -> List[QnARead]:
        qnas = await self.qna_crud.get_qnas_by_portfolio_id(
            portfolio_id=portfolio_id, user_id=current_user.id
        )

        return [
            QnARead(
                id=qna.id,
                status=qna.status,
                portfolio_item_id=qna.portfolio_item_id,
                question=qna.question,
                answer=qna.answer,
            )
            for qna in qnas
        ]

    async def update_qnas(
        self, *, qnas_in: QnAsUpdate, current_user: User
    ) -> List[QnARead]:
        qnas = await self.qna_crud.get_qnas_by_ids(
            ids=[qna.id for qna in qnas_in.qnas], user_id=current_user.id
        )
        update_qna_dict = {qna.id: qna for qna in qnas_in.qnas}

        qnas_to_re_embed = []
        for qna in qnas:
            if qna.status == QnAStatus.CONFIRMED and (
                qna.question != update_qna_dict[qna.id].question
                or qna.answer != update_qna_dict[qna.id].answer
            ):
                qnas_to_re_embed.append(qna)

        if qnas_to_re_embed:
            embeddings = await self.rag_service.embed_qnas(qnas=qnas_to_re_embed)
            embedding_map = {
                qna.id: emb for qna, emb in zip(qnas_to_re_embed, embeddings)
            }
        else:
            embedding_map = {}

        for qna in qnas:
            qna_update = update_qna_dict[qna.id]
            if embedding_map.get(qna.id):
                qna.embedding = embedding_map[qna.id]

            qna.question = qna_update.question
            qna.answer = qna_update.answer

        return [
            QnARead(
                id=qna.id,
                status=qna.status,
                portfolio_item_id=qna.portfolio_item_id,
                question=qna.question,
                answer=qna.answer,
            )
            for qna in qnas
        ]

    async def delete_qnas(self, *, qna_ids: List[uuid.UUID], current_user: User):
        qnas = await self.qna_crud.get_qnas_by_ids(ids=qna_ids, user_id=current_user.id)
        for qna in qnas:
            qna.status = QnAStatus.DELETED

    async def confirm_qnas(
        self, *, qna_ids: List[uuid.UUID], current_user: User
    ) -> List[QnA]:
        qnas = await self.qna_crud.get_qnas_by_ids(ids=qna_ids, user_id=current_user.id)
        embeddings = await self.rag_service.embed_qnas(qnas)

        for qna, embedding in zip(qnas, embeddings):
            qna.embedding = embedding
            qna.status = QnAStatus.CONFIRMED

        return qnas
