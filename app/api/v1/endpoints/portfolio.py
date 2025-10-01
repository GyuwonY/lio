from typing import List
import uuid
from fastapi import (
    APIRouter,
    Depends,
    Body,
    HTTPException,
    status,
    BackgroundTasks,
)

from app.schemas.portfolio_schema import (
    PortfolioRead,
    PortfolioReadWithoutItems,
    PortfolioUpdate,
    PublishedPortfolioRead,
    UploadURLResponse,
    PortfolioCreateFromText,
    PortfolioCreateWithPdf,
    PortfolioCreationResponse,
)
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.portfolio_service import PortfolioService
from app.services.storage_service import StorageService

router = APIRouter()


@router.post("/upload-url", response_model=UploadURLResponse)
async def get_upload_url(
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(),
    *,
    file_name: str = Body(..., embed=True, description="업로드할 파일의 원본 이름"),
) -> UploadURLResponse:
    """
    GCS에 포트폴리오 파일(PDF)을 업로드하기 위한 Presigned URL을 생성합니다.
    """
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드할 수 있습니다.",
        )

    url, file_path = await storage_service.generate_upload_url(
        user_id=current_user.id, file_name=file_name
    )
    return UploadURLResponse(upload_url=url, file_path=file_path)


@router.get("/published/{nickname}", response_model=PublishedPortfolioRead)
async def get_published_portfolio_by_nickname(
    nickname: str,
    service: PortfolioService = Depends(),
) -> PublishedPortfolioRead:
    """
    이메일과 포트폴리오 ID로 PUBLISHED 포트폴리오를 조회합니다. (공개)
    """
    return await service.get_published_portfolio_by_nickname(
        nickname=nickname
    )


@router.post("/text", response_model=PortfolioRead)
async def create_portfolio_from_text(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_in: PortfolioCreateFromText,
) -> PortfolioRead:
    """
    텍스트 입력을 통해 새로운 포트폴리오를 생성하고 즉시 확정합니다.
    """
    return await service.create_portfolio_from_text(
        portfolio_in=portfolio_in, current_user=current_user
    )


@router.post(
    "/pdf",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PortfolioCreationResponse,
)
async def create_portfolio_from_pdf(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_in: PortfolioCreateWithPdf,
) -> PortfolioCreationResponse:
    """
    업로드된 PDF 파일로부터 포트폴리오 생성을 시작합니다.

    1. `/upload-url`을 통해 받은 `file_path`와 포트폴리오 이름을 전달합니다.
    2. 즉시 `DRAFT` 상태의 포트폴리오 정보를 반환하고, 백그라운드에서 PDF 처리 및 분석을 시작합니다.
    3. 작업이 완료되면 FCM을 통해 사용자에게 알림이 전송됩니다.
    """
    draft_portfolio = await service.create_draft_portfolio(
        portfolio_in=portfolio_in, current_user=current_user
    )

    background_tasks.add_task(
        service.create_portfolio_from_pdf_background,
        portfolio_id=draft_portfolio.id,
        user_id=current_user.id,
        file_path=portfolio_in.file_path,
    )

    return PortfolioCreationResponse(
        id=draft_portfolio.id,
        name=draft_portfolio.name,
        status=draft_portfolio.status,
        theme=draft_portfolio.theme
    )


@router.post("/{portfolio_id}/confirm", response_model=PortfolioRead)
async def confirm_portfolio(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_id: uuid.UUID,
) -> PortfolioRead:
    """
    PENDING 상태의 포트폴리오를 CONFIRMED 상태로 확정합니다.
    이 과정에서 각 항목의 임베딩이 생성 및 저장됩니다.
    """
    return await service.confirm_portfolio(
        portfolio_id=portfolio_id, current_user=current_user
    )


@router.post("/{portfolio_id}/publish", response_model=PortfolioReadWithoutItems)
async def publish_portfolio(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_id: uuid.UUID,
) -> PortfolioReadWithoutItems:
    """
    PENDING_QNA 상태의 포트폴리오를 PUBLISHED 상태로 확정합니다.
    기존 PUBLISHED 포트폴리오가 존재하는 경우 PENDING_QNA 로 변경
    """
    return await service.publish_portfolio(
        portfolio_id=portfolio_id, current_user=current_user
    )


@router.get("", response_model=List[PortfolioReadWithoutItems])
async def get_portfolios_by_user(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
) -> List[PortfolioReadWithoutItems]:
    """
    현재 사용자의 모든 포트폴리오 목록을 조회합니다.
    """
    return await service.get_portfolios_by_user(current_user=current_user)


@router.get("/{portfolio_id}", response_model=PortfolioRead)
async def get_portfolio_by_id(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_id: uuid.UUID,
) -> PortfolioRead:
    """
    ID로 특정 포트폴리오를 조회합니다.
    """
    return await service.get_portfolio_by_id(
        portfolio_id=portfolio_id, current_user=current_user
    )


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_id: uuid.UUID,
):
    """
    ID로 특정 포트폴리오를 삭제합니다.
    """
    return await service.delete_portfolio(
        portfolio_id=portfolio_id, current_user=current_user
    )


@router.put("/{portfolio_id}", response_model=PortfolioReadWithoutItems)
async def update_portfolio(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_id: uuid.UUID,
    portfolio_update: PortfolioUpdate,
) -> PortfolioReadWithoutItems:
    return await service.update_portfolio(
        current_user=current_user,
        portfolio_id=portfolio_id,
        portfolio_update=portfolio_update,
    )
    
@router.put("/publish", response_model=PortfolioReadWithoutItems)
async def get_published_portfolios(
    service: PortfolioService = Depends(),
) -> PortfolioReadWithoutItems:
    return await service.get_published_portfolios()

