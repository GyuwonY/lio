from fastapi import APIRouter, Depends, status, Response
from app.schemas.chat_session_schema import ChatSessionCreate, ChatSessionCreateResponse
from app.services.chat_session_service import ChatSessionService

router = APIRouter()


@router.post(
    "", response_model=ChatSessionCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    response: Response,
    session_service: ChatSessionService = Depends(),
    *,
    creat_session_request: ChatSessionCreate,
):
    chat_session = await session_service.create_session(
        portfolio_id=creat_session_request.portfolio_id,
        user_id=creat_session_request.user_id,
    )

    response.set_cookie(
        key="session_id",
        value=chat_session.session_id,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=session_service.context_expire_time,
    )
    return ChatSessionCreateResponse(chat_session_id=chat_session.id)
