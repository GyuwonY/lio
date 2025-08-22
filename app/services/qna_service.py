import asyncio
from typing import List
from fastapi import Depends, BackgroundTasks, HTTPException, status

from app.crud.qna_crud import QnACRUD
from app.crud.portfolio_crud import PortfolioCRUD
from app.models.portfolio import PortfolioStatus
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
        portfolio_crud: PortfolioCRUD = Depends(),
        llm_service: LLMService = Depends(),
        rag_service: RAGService = Depends(),
    ):
        self.qna_crud = qna_crud
        self.portfolio_crud = portfolio_crud
        self.llm_service = llm_service
        self.rag_service = rag_service


    async def _generate_and_save_qna_for_item(
        self, *, item: PortfolioItem, user_id: int
    ):
        try:
            parsed_output = await self.llm_service.generate_qna_for_portfolio_item(
                item=item
            )

            if not parsed_output.qnas:
                print(f"No QnA generated for portfolio_item_id: {item.id}")
                return

            qnas_to_create = [
                QnACreate(
                    question=qna_set.question,
                    answer=qna_set.answer,
                    portfolio_item_id=item.id,
                )
                for qna_set in parsed_output.qnas
            ]

            await self.qna_crud.bulk_create_qnas(
                qna_list=qnas_to_create, user_id=user_id
            )

        except Exception as e:
            print(f"Error generating QnA for portfolio_item_id {item.id}: {e}")


    async def generate_qna_for_all_portfolios_background(self, *, current_user: User, portfolio_id: int):
        user_portfolio = await self.portfolio_crud.get_portfolio_by_id(
            user_id=current_user.id, portfolio_id=portfolio_id
        )
        
        if not user_portfolio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="존재하지 않는 포트폴리오",
            )
        
        if user_portfolio.status != PortfolioStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="확정되지 않은 포트폴리오",
            )

        all_items = [item for item in user_portfolio.items]

        if not all_items:
            print(f"No portfolio items found for user_id: {current_user.id}")
            return

        tasks = [
            self._generate_and_save_qna_for_item(item=item, user_id=current_user.id)
            for item in all_items
        ]
        await asyncio.gather(*tasks)


    async def add_qna_generation_task(
        self, *, background_tasks: BackgroundTasks, current_user: User, portfolio_id: int
    ) -> dict:
        background_tasks.add_task(
            self.generate_qna_for_all_portfolios_background, current_user=current_user, portfolio_id=portfolio_id
        )
        return {"message": "Q&A generation has been started in the background."}


    async def get_qnas_by_portfolio(
        self, *, portfolio_id: int, current_user: User
    ) -> List[QnARead]:
        qnas = await self.qna_crud.get_qnas_by_portfolio_id(portfolio_id=portfolio_id, user_id=current_user.id)

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
        
        qnas = await self.qna_crud.get_qnas_by_ids(ids=[qna.id for qna in qnas_in.qnas], user_id=current_user.id)
        update_qna_dict = {qna.id:qna for qna in qnas_in.qnas}
        
        qnas_to_re_embed = []
        for qna in qnas:
            if (
                qna.status == QnAStatus.CONFIRMED
                and (qna.question != update_qna_dict[qna.id].question or qna.answer != update_qna_dict[qna.id].answer)
            ):
                qnas_to_re_embed.append(qna)

        if qnas_to_re_embed:
            embeddings = await self.rag_service.embed_qnas(
                qnas=qnas_to_re_embed
            )
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
        
        
        for qna in qnas:
            update_qna = update_qna_dict[qna.id]
            qna.question = update_qna.question
            qna.answer = update_qna.answer
        
        return [QnARead(
                id=qna.id,
                status=qna.status,
                portfolio_item_id=qna.portfolio_item_id,
                question=qna.question,
                answer=qna.answer,
            ) for qna in qnas]

    
    async def delete_qnas(self, *, qna_ids: List[int], current_user: User):
        qnas = await self.qna_crud.get_qnas_by_ids(ids=qna_ids, user_id=current_user.id)
        for qna in qnas:
            qna.status = QnAStatus.DELETED
            
    
    async def confirm_qnas(self, *, qna_ids: List[int], current_user: User) -> List[QnA]:
        qnas = await self.qna_crud.get_qnas_by_ids(ids=qna_ids, user_id=current_user.id)
        embeddings = await self.rag_service.embed_qnas(qnas)
        
        for qna, embedding in zip(qnas, embeddings):
            qna.embedding = embedding
            qna.status = QnAStatus.CONFIRMED
            
        return qnas
