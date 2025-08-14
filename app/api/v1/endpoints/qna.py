from fastapi import APIRouter, Depends
from typing import List

from app.schemas.qna_schema import QnACreate, QnARead, QnAUpdate
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.qna_service import QnAService

router = APIRouter()


@router.post("/generate", status_code=201, summary="포트폴리오 기반 Q&A 생성")
async def generate_qna(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
    *,
    qna_in: QnACreate,
):
    return await service.generate_qna_from_portfolios(
        portfolio_ids=qna_in.portfolio_ids, current_user=current_user
    )


@router.get("/", response_model=List[QnARead], summary="내 Q&A 목록 조회")
async def get_my_qna(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
):
    return await service.get_user_qnas(current_user=current_user)


@router.patch("/{qna_id}", response_model=QnARead, summary="Q&A 수정 및 확정")
async def update_my_qna(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
    *,
    qna_id: int,
    qna_in: QnAUpdate,
):
    return await service.update_qna(
        qna_id=qna_id, qna_in=qna_in, current_user=current_user
    )
