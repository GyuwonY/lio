from fastapi import APIRouter, Depends, Request
from app.schemas.chat_schema import ChatCreate, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def run_chat(
    request: Request,
    chat_service: ChatService = Depends(),
    *,
    chat_create: ChatCreate,
    
):
    """
    LangGraph 기반 챗봇을 실행합니다.
    """
    final_state = await chat_service.run_chat(
        chat_create=chat_create, ip=request.client.host
    )
    return ChatResponse(answer=final_state["final_answer"])


