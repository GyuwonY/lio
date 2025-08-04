import re
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.crud.qna import QnACRUD
from app.schemas.qna import QnAUpdate
from app.models.user import User
from app.models.qna import QnA
from app.services.llm_service import LLMService


class QnAService:
    def __init__(self, crud: QnACRUD, llm_service: LLMService):
        self.crud = crud
        self.llm_service = llm_service

    async def get_user_qnas(self, db: AsyncSession, *, current_user: User) -> List[QnA]:
        return await self.crud.get_qnas_by_user(db=db, user=current_user)

    async def generate_qna_from_portfolios(
        self, db: AsyncSession, *, portfolio_ids: list[int], current_user: User
    ) -> dict:
        generated_text = await self.llm_service.generate_qna_from_portfolios(
            portfolio_ids=portfolio_ids, user_id=current_user.id
        )
        qna_pairs = re.findall(r"Q:(.*?) A:(.*?)(?=Q:|$)", generated_text, re.DOTALL)
        if not qna_pairs:
            raise HTTPException(
                status_code=500, detail="Failed to parse Q&A from LLM response."
            )

        created_qnas = []
        for q, a in qna_pairs:
            qna_obj = await self.crud.create_qna(
                db=db, question=q.strip(), answer=a.strip(), user=current_user
            )
            created_qnas.append(qna_obj)

        return {
            "message": f"{len(created_qnas)} Q&A pairs have been generated successfully."
        }

    async def update_qna(
        self, db: AsyncSession, *, qna_id: int, qna_in: QnAUpdate, current_user: User
    ) -> QnA:
        db_qna = await self.crud.get_qna_by_id(db=db, qna_id=qna_id)
        if not db_qna or db_qna.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Q&A not found."
            )

        updated_qna = await self.crud.update_qna(db=db, db_obj=db_qna, obj_in=qna_in)
        # TODO: 확정된 Q&A Weaviate 저장 로직 추가
        return updated_qna
