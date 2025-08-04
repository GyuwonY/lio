from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.token import Token
from app.services.auth_service import get_current_user_from_refresh_token
from app.models.user import User
from app.services.auth_service import AuthService
from app.crud.user import UserCRUD
from app.core.dependencies import get_auth_service, get_user_crud
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()


@router.post("/google", response_model=Token, tags=["Authentication"])
async def login_with_google(
    *,
    db: AsyncSession = Depends(get_db),
    id_token: str = Body(..., embed=True, alias="idToken"),
    auth_service: AuthService = Depends(get_auth_service),
    user_crud: UserCRUD = Depends(get_user_crud)
):
    return await auth_service.login_or_register_google(
        db=db, id_token=id_token, userCRUD=user_crud
    )


@router.post("/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(
    current_user: User = Depends(get_current_user_from_refresh_token),
):
    return {
        "access_token": create_access_token(subject=current_user.email),
        "refresh_token": create_refresh_token(subject=current_user.email),
        "token_type": "bearer",
    }
