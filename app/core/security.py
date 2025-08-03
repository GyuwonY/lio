from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    주어진 데이터로 JWT 액세스 토큰을 생성합니다.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_google_id_token(*, token: str) -> Optional[dict[str, Any]]:
    """
    Google ID 토큰을 검증하고 사용자 정보를 반환합니다.
    """
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
