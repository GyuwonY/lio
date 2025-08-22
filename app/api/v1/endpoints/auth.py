from fastapi import APIRouter, Depends, Body
from app.schemas.token_schema import Token
from app.models.user import User
from app.services.auth_service import AuthService, get_current_user_from_refresh_token

router = APIRouter()


@router.post("/google", response_model=Token, tags=["Authentication"])
async def login_with_google(
    auth_service: AuthService = Depends(),
    *,
    id_token: str = Body(..., embed=True),
):
    return await auth_service.login_or_register_google(id_token=id_token)


@router.post("/refresh", response_model=Token, tags=["Authentication"])
async def refresh_token(
    current_user: User = Depends(get_current_user_from_refresh_token),
    auth_service: AuthService = Depends(),
):
    return {
        "access_token": auth_service.create_access_token(subject=current_user.email),
        "refresh_token": auth_service.create_refresh_token(subject=current_user.email),
        "token_type": "bearer",
    }
