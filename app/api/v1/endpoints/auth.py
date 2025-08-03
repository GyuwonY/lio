from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, Token
from app.crud import user as crud_user
from app.core.security import create_access_token, verify_google_id_token

router = APIRouter()

@router.post("/google", response_model=Token, tags=["Authentication"])
async def login_with_google(
    *,
    db: AsyncSession = Depends(get_db),
    id_token: str = Body(..., embed=True, alias="idToken")
):
    """
    Google ID 토큰을 사용하여 로그인/회원가입을 처리하고 JWT를 발급합니다.
    - **idToken**: 프론트엔드에서 받은 Google ID 토큰.
    """
    # Google 토큰 검증은 CPU-bound 작업이므로 동기 함수 그대로 사용 가능
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

    user = await crud_user.get_user_by_email(db=db, email=email)
    if not user:
        user_in = UserCreate(
            email=email,
            full_name=google_user_info.get("name")
        )
        user = await crud_user.create_user(db=db, user_in=user_in)

    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
