import asyncio
import uuid
from typing import List
from fastapi import BackgroundTasks, Depends

from app.db.session import AsyncSessionLocal
from app.crud.portfolio_item_crud import PortfolioItemCRUD
from app.crud.qna_crud import QnACRUD
from app.models.qna import QnA, QnAStatus
from app.schemas.qna_schema import (
    QnARead,
    QnACreate,
    QnAsUpdate,
)
from app.models.user import User
from app.models.portfolio_item import PortfolioItem
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService


class QnAService:
    def __init__(
        self,
        qna_crud: QnACRUD = Depends(),
        llm_service: LLMService = Depends(),
        rag_service: RAGService = Depends(),
        portfolio_item_crud: PortfolioItemCRUD = Depends(),
    ):
        self.qna_crud = qna_crud
        self.portfolio_item_crud = portfolio_item_crud
        self.llm_service = llm_service
        self.rag_service = rag_service

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
        user_id: uuid.UUID,
        portfolio_id: uuid.UUID,
    ):
        async with AsyncSessionLocal() as db:
            try:
                portfolio_item_crud = PortfolioItemCRUD(db)
                qna_crud = QnACRUD(db)

                portfolio_items = (
                    await portfolio_item_crud.get_confirmed_portfolio_items_by_portfolio_id(
                        portfolio_id=portfolio_id
                    )
                )

                if not portfolio_items:
                    print(
                        f"No confirmed portfolio items found for portfolio_id: {portfolio_id}"
                    )
                    return

                tasks = [
                    self._generate_qna_for_item(item=item) for item in portfolio_items
                ]
                results = await asyncio.gather(*tasks)

                qnas_to_create = []
                for result in results:
                    qnas_to_create.extend(result)

                if qnas_to_create:
                    await qna_crud.bulk_create_qnas(
                        qna_list=qnas_to_create, user_id=user_id
                    )
                await db.commit()
            except Exception as e:
                await db.rollback()
                print(f"Error generating QnA for portfolio {portfolio_id}: {e}")

    async def add_qna_generation_task(
        self,
        *,
        background_tasks: BackgroundTasks,
        current_user: User,
        portfolio_id: uuid.UUID,
    ) -> dict:
        background_tasks.add_task(
            self.generate_qna_for_all_portfolios_background,
            user_id=current_user.id,
            portfolio_id=portfolio_id,
        )
        return {"message": "Q&A generation has been started in the background."}

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
