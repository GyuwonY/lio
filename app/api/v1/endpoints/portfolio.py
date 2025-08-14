from typing import List, Any, TYPE_CHECKING
from fastapi import APIRouter, Depends, Body, HTTPException, status, Response

from app.schemas.portfolio_schema import PortfolioRead, PortfolioCreate, UploadURLResponse
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.portfolio_service import PortfolioService
from app.services.storage_service import StorageService
from app.models.portfolio import Portfolio
    

router = APIRouter()

@router.post("/upload-url", response_model=UploadURLResponse)
async def get_upload_url(
    *,
    current_user: User = Depends(get_current_user),
    file_name: str = Body(..., embed=True, description="업로드할 파일의 원본 이름"),
    storage_service: StorageService = Depends(),
) -> UploadURLResponse:
    """
    GCS에 포트폴리오 파일(PDF 등)을 업로드하기 위한 Presigned URL을 생성합니다.
    """
    if not file_name.lower().endswith((".pdf", ".txt")): # txt도 허용
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 또는 TXT 파일만 업로드할 수 있습니다.",
        )
    
    url, file_path = await storage_service.generate_upload_url(
        user_id=current_user.id, file_name=file_name
    )
    return UploadURLResponse(upload_url=url, file_path=file_path)


@router.post("/", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    *,
    portfolio_in: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
) -> Any:
    """
    새로운 포트폴리오를 생성합니다.

    - **PDF 파일로부터 생성**: `file_url` (GCS 경로)를 제공하세요.
    - **텍스트로부터 생성**: `text_items` 리스트를 제공하세요.

    `file_url`과 `text_items` 중 하나만 사용해야 합니다.
    """
    try:
        created_portfolio = await service.create_portfolio(
            portfolio_in=portfolio_in, current_user=current_user
        )
        return created_portfolio
    except ValueError as e:
        # 스키마 레벨에서 이미 검증하지만, 서비스 로직에서도 에러 발생 가능
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[PortfolioRead])
async def read_portfolios(
    *,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
) -> Any:
    """
    현재 사용자의 모든 포트폴리오 목록을 조회합니다.
    """
    return await service.get_user_portfolios(current_user=current_user)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    *,
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
):
    """
    ID로 특정 포트폴리오를 삭제합니다.
    """
    await service.delete_portfolio(portfolio_id=portfolio_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)