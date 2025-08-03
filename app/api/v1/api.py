from fastapi import APIRouter
from app.api.v1.endpoints import auth, portfolios, chat

api_router = APIRouter()

# auth 라우터 포함
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# portfolios 라우터 포함
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])

# chat 라우터 포함
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])

