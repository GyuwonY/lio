import uuid
from fastapi import APIRouter, Depends
from typing import List

from app.models.portfolio_item import PortfolioItemType
from app.schemas.qna_schema import QnARead, QnAsConfirm, QnAsDelete, QnAsUpdate
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.qna_service import QnAService

router = APIRouter()


# @router.post(
#     "/generate",
#     summary="포트폴리오 기반 Q&A 생성 (백그라운드)",
# )
# async def generate_qna(
#     background_tasks: BackgroundTasks,
#     current_user: User = Depends(get_current_user),
#     service: QnAService = Depends(),
#     *,
#     portfolio_id: uuid.UUID,
#     portfolio_item_type: PortfolioItemType
# ):
#     """
#     사용자의 모든 포트폴리오 항목에 대한 Q&A 생성을 백그라운드 작업으로 시작합니다.
#     API는 즉시 응답을 반환하며, 실제 생성 작업은 백그라운드에서 수행됩니다.
#     """
#     return await service.add_qna_generation_task(
#         background_tasks=background_tasks, current_user=current_user, portfolio_id=portfolio_id, portfolio_item_type=portfolio_item_type
#     )


@router.post(
    "/generate",
    summary="포트폴리오 기반 Q&A 생성",
    response_model=List[QnARead],
)
async def generate_qna_sync(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
    *,
    portfolio_id: uuid.UUID,
    portfolio_item_type: PortfolioItemType,
):
    """
    사용자의 모든 포트폴리오 항목에 대한 Q&A 생성을 동기적으로 수행합니다.
    API는 모든 생성이 완료될 때까지 기다린 후 응답을 반환합니다.
    """
    return await service.generate_qna_for_all_portfolios_background(
        current_user=current_user,
        portfolio_id=portfolio_id,
        portfolio_item_type=portfolio_item_type,
    )


@router.get("/{portfolio_id}", response_model=List[QnARead], summary="내 Q&A 목록 조회")
async def get_qnas_by_portfolio(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
    *,
    portfolio_id: uuid.UUID,
):
    return await service.get_qnas_by_portfolio(
        current_user=current_user, portfolio_id=portfolio_id
    )


@router.put("/confirm", response_model=List[QnARead], summary="Q&A 확정")
async def confirm_qnas(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
    *,
    qnas_confirm: QnAsConfirm,
):
    return await service.confirm_qnas(
        qna_ids=qnas_confirm.qna_ids, current_user=current_user
    )


@router.put("/bulk", response_model=List[QnARead], summary="Q&A 벌크 수정")
async def update_qnas(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
    *,
    qnas_in: QnAsUpdate,
):
    return await service.update_qnas(qnas_in=qnas_in, current_user=current_user)


@router.delete("/", response_model=List[QnARead], summary="Q&A 벌크 삭제")
async def delete_qnas(
    current_user: User = Depends(get_current_user),
    service: QnAService = Depends(),
    *,
    qnas_delete: QnAsDelete,
):
    return await service.delete_qnas(
        qna_ids=qnas_delete.qna_ids, current_user=current_user
    )
