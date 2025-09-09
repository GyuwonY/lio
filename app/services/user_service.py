from fastapi import Depends
from app.crud.user_crud import UserCRUD
from app.models.user import User
from app.schemas.user_schema import UserRead, UserUpdate


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
        current_user.nickname = user_update.nickname

        return UserRead.model_validate(current_user)
