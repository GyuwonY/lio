from fastapi import APIRouter, Depends, Body
from app.schemas.token_schema import Token
from app.models.user import User
from app.schemas.user_schema import UserRead
from app.services.auth_service import (
    AuthService,
    get_current_user,
    get_current_user_from_refresh_token,
)

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


@router.get("/user", response_model=UserRead)
async def get_user_from_token(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        picture=current_user.picture,
        locale=current_user.locale,
        created_at=current_user.created_at,
    )
