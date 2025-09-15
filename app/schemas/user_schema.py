import uuid
from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
    job: Optional[str] = None
    address: Optional[str] = None
    nickname: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime


class UserUpdate(BaseModel):
    job: Optional[str] = None
    address: Optional[str] = None
    nickname: Optional[str] = None


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    
    
class CheckNickname(BaseModel):
    nickname: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[EmailStr] = None
