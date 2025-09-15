from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.user_schema import CheckNickname, UserRead, UserUpdate
from app.services.auth_service import get_current_user
from app.services.user_service import UserService


router = APIRouter()


@router.put("", response_model=UserRead)
async def update_user(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(),
    *,
    user_update: UserUpdate,
) -> UserRead:
    return await user_service.update_user(
        current_user=current_user, user_update=user_update
    )


@router.get("/check/nickname")
async def check_nickname(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(),
    *,
    nickname: str,
):
    return await user_service.check_nickname(
        nickname = nickname
    )


