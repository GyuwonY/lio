from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings
from app.schemas.token import TokenPayload


def create_access_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.ACCESS_TOKEN_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, secret_key: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None


def verify_google_id_token(*, token: str) -> Optional[dict[str, Any]]:
    try:
        id_info = id_token.verify_oauth2_token(
            token, requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        return id_info
    except ValueError:
        # 잘못된 토큰
        return None
    except Exception as e:
        # 기타 예외 처리
        print(f"An unexpected error occurred during token verification: {e}")
        return None
