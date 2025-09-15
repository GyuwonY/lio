from fastapi import Depends, HTTPException, status
from app.crud.user_crud import UserCRUD
from app.models.user import User
from app.schemas.user_schema import CheckNickname, UserRead, UserUpdate


class UserService:
    def __init__(
        self,
        user_crud: UserCRUD = Depends(),
    ):
        self.user_crud = user_crud

    async def update_user(
        self, *, current_user: User, user_update: UserUpdate
    ) -> UserRead:
        current_user.address = user_update.address
        current_user.job = user_update.job
        
        if user_update.nickname and current_user.nickname != user_update.nickname:
            duplicate_user = await self.user_crud.get_user_by_nickname(nickname=user_update.nickname)
            if not duplicate_user:
                current_user.nickname = user_update.nickname

        return UserRead.model_validate(current_user)
    
    
    async def check_nickname(self, *, checkNickname: CheckNickname):
        duplicate_user = await self.user_crud.get_user_by_nickname(nickname=checkNickname.nickname)
        if duplicate_user:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드할 수 있습니다.",
        )
