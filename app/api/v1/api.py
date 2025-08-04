from fastapi import APIRouter
from app.api.v1.endpoints import auth, portfolios, qna, chatbot_setting, chat

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

api_router.include_router(portfolios.router, prefix="/portfolios", tags=["Portfolios"])

api_router.include_router(qna.router, prefix="/qna", tags=["Q&A and Chat"])

api_router.include_router(
    chatbot_setting.router, prefix="/chatbot-settings", tags=["Chatbot Settings"]
)

api_router.include_router(
    chat.router, prefix="/chat", tags=["Chat"]
)
