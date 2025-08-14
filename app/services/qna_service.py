from typing import List
from fastapi import HTTPException, status, Depends

from app.crud.qna_crud import QnACRUD
from app.schemas.qna_schema import QnAUpdate
from app.models.user import User
from app.models.qna import QnA
from app.services.llm_service import LLMService


class QnAService:
    def __init__(
        self,
        crud: QnACRUD = Depends(),
        llm_service: LLMService = Depends(),
    ):
        self.crud = crud
        self.llm_service = llm_service

    async def get_user_qnas(self, *, current_user: User) -> List[QnA]:
        return await self.crud.get_qnas_by_user(user=current_user)

    async def generate_qna_from_portfolios(
        self, *, portfolio_ids: list[int], current_user: User
    ) -> dict:

        return {
            "message": "Q&A pairs have been generated successfully."
        }

    async def update_qna(
        self, *, qna_id: int, qna_in: QnAUpdate, current_user: User
    ) -> QnA:
        db_qna = await self.crud.get_qna_by_id(qna_id=qna_id)
        if not db_qna or db_qna.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Q&A not found."
            )

        updated_qna = await self.crud.update_qna(db_obj=db_qna, obj_in=qna_in)
        # TODO: 확정된 Q&A Weaviate 저장 로직 추가
        return updated_qna
