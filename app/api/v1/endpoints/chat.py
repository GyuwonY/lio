from fastapi import APIRouter, Depends, Cookie, HTTPException, status
from app.schemas.chat_schema import ChatCreate, ChatResponse
from app.services.chat_service import ChatService
from typing import Annotated

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def run_chat(
    chat_service: ChatService = Depends(),
    session_id: Annotated[str | None, Cookie()] = None,
    *,
    chat_create: ChatCreate,
):
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session ID not found in cookies",
        )
        
    final_state = await chat_service.run_chat(
        chat_create=chat_create, session_id=session_id
    )
    return ChatResponse(
        answer=final_state.final_answer,
        session_id=session_id
    )


