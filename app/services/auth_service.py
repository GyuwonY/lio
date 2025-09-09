from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests

from app.crud.user_crud import UserCRUD
from app.schemas.user_schema import UserCreate
from app.schemas.token_schema import TokenPayload
from app.core.config import settings
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


class AuthService:
    def __init__(self, user_crud: UserCRUD = Depends()):
        self.user_crud = user_crud

    def _create_token(
        self, subject: Any, secret_key: str, expires_in_minutes: int
    ) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        to_encode = {"exp": expire, "sub": str(subject)}
        return jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)

    def create_access_token(self, subject: Any) -> str:
        return self._create_token(
            subject,
            settings.ACCESS_TOKEN_SECRET_KEY,
            settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    def create_refresh_token(self, subject: Any) -> str:
        return self._create_token(
            subject,
            settings.REFRESH_TOKEN_SECRET_KEY,
            settings.REFRESH_TOKEN_EXPIRE_MINUTES,
        )

    def _verify_token(self, *, token: str, secret_key: str) -> Optional[TokenPayload]:
        try:
            payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
            return TokenPayload(**payload)
        except JWTError:
            return None

    def _verify_google_id_token(self, *, token: str) -> Optional[dict[str, Any]]:
        try:
            return id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return None
        except Exception as e:
            print(f"An unexpected error occurred during token verification: {e}")
            return None

    async def login_or_register_google(self, *, id_token: str) -> dict:
        google_user_info = self._verify_google_id_token(token=id_token)
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

        user = await self.user_crud.get_user_by_email(email=email)
        if not user:
            user_in = UserCreate(
                email=email,
                first_name=google_user_info.get("given_name"),
                last_name=google_user_info.get("family_name"),
                picture=google_user_info.get("picture"),
                locale=google_user_info.get("locale"),
            )
            user = await self.user_crud.create_user(user_in=user_in)

        return {
            "access_token": self.create_access_token(subject=user.email),
            "refresh_token": self.create_refresh_token(subject=user.email),
            "token_type": "bearer",
        }

    async def get_user_from_token(self, *, token: str, secret_key: str) -> User:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        token_payload = self._verify_token(token=token, secret_key=secret_key)
        if token_payload is None or token_payload.sub is None:
            raise credentials_exception

        user = await self.user_crud.get_user_by_email(email=token_payload.sub)
        if user is None:
            raise credentials_exception
        return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(),
) -> User:
    """Dependency to get user from access token."""
    return await auth_service.get_user_from_token(
        token=token, secret_key=settings.ACCESS_TOKEN_SECRET_KEY
    )


async def get_current_user_from_refresh_token(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(),
) -> User:
    """Dependency to get user from refresh token."""
    return await auth_service.get_user_from_token(
        token=token, secret_key=settings.REFRESH_TOKEN_SECRET_KEY
    )
