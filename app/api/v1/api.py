from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    portfolio,
    qna,
    chatbot_setting,
    portfolio_item,
    chat_message,
    chat_session,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(auth.router, prefix="/user", tags=["User"])
api_router.include_router(chat_session.router, prefix="/chat-session", tags=["Session"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])
api_router.include_router(
    portfolio_item.router, prefix="/portfolio-item", tags=["Portfolio Item"]
)
api_router.include_router(qna.router, prefix="/qna", tags=["Q&A and Chat"])
api_router.include_router(
    chatbot_setting.router, prefix="/chatbot-setting", tags=["Chatbot Setting"]
)

api_router.include_router(chat_message.router, prefix="/chat-message", tags=["Chat"])
