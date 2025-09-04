from fastapi import APIRouter, Depends, Cookie, HTTPException, status
from app.schemas.chat_message_schema import ChatMessageCreate, ChatMessageResponse
from app.services.chat_message_service import ChatMessageService
from typing import Annotated

router = APIRouter()


@router.post("/", response_model=ChatMessageResponse)
async def run_chat(
    chat_service: ChatMessageService = Depends(),
    session_id: Annotated[str | None, Cookie()] = None,
    *,
    chat_create: ChatMessageCreate,
):
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session ID not found in cookies",
        )
        
    answer = await chat_service.run_chat(
        chat_create=chat_create, session_id=session_id
    )
    return ChatMessageResponse(
        answer=answer,
        session_id=session_id
    )


