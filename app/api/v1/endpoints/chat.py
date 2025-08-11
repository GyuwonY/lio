from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.agent_service import AgentService


router = APIRouter()


@router.post("/{user_email}", summary="공개 챗봇에게 질문")
async def ask_public_chatbot(
    user_email: str,
    *,
    question: str = Body(..., embed=True),
    agent_service: AgentService = Depends(),
):
    result = await agent_service.ask_question(user_email=user_email, question=question)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
