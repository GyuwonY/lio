from typing import List, Any
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel

from app.schemas.portfolio import PortfolioRead, PortfolioCreate
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.portfolio_service import PortfolioService

router = APIRouter()


class PresignedURLResponse(BaseModel):
    upload_url: str
    file_path: str


@router.post("/presigned-url", response_model=PresignedURLResponse)
async def get_presigned_url(
    *,
    current_user: User = Depends(get_current_user),
    file_name: str = Body(..., embed=True),
    service: PortfolioService = Depends(),
) -> Any:
    """
    Get a presigned URL for uploading a portfolio file.
    """
    return service.generate_presigned_url(
        file_name=file_name, current_user=current_user
    )


@router.post("/", response_model=PortfolioRead, status_code=201)
async def create_portfolio(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
    *,
    portfolio_in: PortfolioCreate,
) -> Any:
    """
    Create a new portfolio record in the database after the file has been uploaded to GCS.
    """
    return await service.create_portfolio(
        file_name=portfolio_in.file_name,
        file_path=portfolio_in.file_path,
        current_user=current_user,
    )


@router.get("/", response_model=List[PortfolioRead])
async def read_portfolios(
    current_user: User = Depends(get_current_user),
    service: PortfolioService = Depends(),
):
    """
    Retrieve all portfolios for the current user.
    """
    return await service.get_user_portfolios(current_user=current_user)
