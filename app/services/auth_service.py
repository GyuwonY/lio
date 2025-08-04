from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.crud.user import UserCRUD
from app.schemas.user import UserCreate
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_google_id_token,
    verify_token,
)
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class AuthService:
    async def login_or_register_google(
        self, db: AsyncSession, *, id_token: str, userCRUD: UserCRUD
    ) -> dict:
        google_user_info = verify_google_id_token(token=id_token)
        if not google_user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google ID token.",
            )

        email = google_user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token.",
            )

        user = await userCRUD.get_user_by_email(db=db, email=email)
        if not user:
            user_in = UserCreate(email=email, full_name=google_user_info.get("name"))
            user = await userCRUD.create_user(db=db, user_in=user_in)

        return {
            "access_token": create_access_token(subject=user.email),
            "refresh_token": create_refresh_token(subject=user.email),
            "token_type": "bearer",
        }


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    user_crud: UserCRUD = Depends(UserCRUD),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_payload = verify_token(token, settings.ACCESS_TOKEN_SECRET_KEY)
    if token_payload is None or token_payload.sub is None:
        raise credentials_exception

    user = await user_crud.get_user_by_email(db, email=token_payload.sub)
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_from_refresh_token(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    user_crud: UserCRUD = Depends(UserCRUD),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_payload = verify_token(token, settings.REFRESH_TOKEN_SECRET_KEY)
    if token_payload is None or token_payload.sub is None:
        raise credentials_exception

    user = await user_crud.get_user_by_email(db, email=token_payload.sub)
    if user is None:
        raise credentials_exception
    return user

