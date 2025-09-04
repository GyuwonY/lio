import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, Body, HTTPException, status

from app.schemas.portfolio_schema import (
    PortfolioRead,
    PortfolioUpdate,
    UploadURLResponse,
    PortfolioCreateFromText,
    PortfolioCreateWithPdf,
    PortfolioConfirm,
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


@router.get("/{email}/{portfolio_id}", response_model=PortfolioRead)
async def get_portfolio_by_email_and_id(
    email: str,
    portfolio_id: uuid.UUID,
    service: PortfolioService = Depends(),
) -> PortfolioRead:
    """
    이메일과 포트폴리오 ID로 특정 포트폴리오를 조회합니다. (공개)
    """
    return await service.get_portfolio_by_email_and_id(
        email=email, portfolio_id=portfolio_id
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


@router.post("/pdf", response_model=PortfolioRead)
async def create_portfolio_from_pdf(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    upload_response: UploadURLResponse,
) -> PortfolioRead:
    """
    업로드된 PDF 파일로부터 PENDING 상태의 포트폴리오를 생성합니다.

    1. `/upload-url`을 통해 받은 `file_path`를 사용합니다.
    2. 생성된 포트폴리오는 사용자의 확인을 기다리는 `PENDING` 상태가 됩니다.
    """
    portfolio_in = PortfolioCreateWithPdf(file_path=upload_response.file_path)
    return await service.create_portfolio_from_pdf(
        portfolio_in=portfolio_in, current_user=current_user
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
    confirm_in = PortfolioConfirm(portfolio_id=portfolio_id)
    return await service.confirm_portfolio(
        confirm_in=confirm_in, current_user=current_user
    )


@router.get("/", response_model=List[PortfolioRead])
async def get_portfolios_by_user(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
) -> List[PortfolioRead]:
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
    return await service.delete_portfolio(portfolio_id=portfolio_id, current_user=current_user)



@router.put("/{portfolio_id}", response_model=PortfolioRead)
async def update_portfolio(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_id: uuid.UUID,
    portfolio_update: PortfolioUpdate
) -> PortfolioRead:
    return await service.update_portfolio(current_user=current_user, portfolio_id=portfolio_id, portfolio_update=portfolio_update)
