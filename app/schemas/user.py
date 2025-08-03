from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional

# --- User Schemas ---

class UserBase(BaseModel):
    """공통 사용자 필드"""
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """사용자 생성을 위한 스키마"""
    pass

class UserRead(UserBase):
    """사용자 조회를 위한 스키마 (API 응답용)"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Token Schemas ---

class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """JWT 토큰 내부에 저장될 데이터 스키마"""
    email: Optional[EmailStr] = None
