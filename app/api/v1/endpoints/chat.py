from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import re
import json

from app.db.session import get_db
from app.schemas.qa import QACreate, QARead, QAUpdate
from app.schemas.setting import ChatbotSettingRead, ChatbotSettingUpdate
from app.crud import qa as crud_qa
from app.crud import setting as crud_setting
from app.crud import user as crud_user
from app.models.user import User
from app.models.qa import QAStatus
from app.core.dependencies import get_current_user
from app.services import llm_service, agent_service

router = APIRouter()

# --- Q&A Endpoints ---

@router.post("/qna/generate", status_code=status.HTTP_201_CREATED, summary="포트폴리오 기반 Q&A 생성")
async def generate_qna(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    qna_in: QACreate
):
    generated_text = await llm_service.generate_qna_from_portfolios(
        portfolio_ids=qna_in.portfolio_ids,
        owner_id=current_user.id
    )
    qna_pairs = re.findall(r"Q:(.*?) A:(.*?)(?=
Q:|
)", generated_text, re.DOTALL)
    if not qna_pairs:
        raise HTTPException(status_code=500, detail="Failed to parse Q&A from LLM response.")
    
    created_qas = []
    for q, a in qna_pairs:
        qa_obj = await crud_qa.create_qa(db=db, question=q.strip(), answer=a.strip(), owner=current_user)
        created_qas.append(qa_obj)

    return {"message": f"{len(created_qas)} Q&A pairs have been generated successfully."}


@router.get("/qna", response_model=List[QARead], summary="내 Q&A 목록 조회")
async def get_my_qna(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await crud_qa.get_qas_by_owner(db=db, owner=current_user)


@router.patch("/qna/{qa_id}", response_model=QARead, summary="Q&A 수정 및 확정")
async def update_my_qna(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    qa_id: int,
    qa_in: QAUpdate
):
    db_qa = await crud_qa.get_qa_by_id(db=db, qa_id=qa_id)
    if not db_qa or db_qa.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Q&A not found.")

    updated_qa = await crud_qa.update_qa(db=db, db_obj=db_qa, obj_in=qa_in)

    if updated_qa.status == QAStatus.CONFIRMED:
        # TODO: 확정된 Q&A를 Weaviate에 저장하는 로직 추가
        pass
    return updated_qa

# --- Chatbot Settings Endpoints ---

@router.get("/settings", response_model=ChatbotSettingRead, summary="챗봇 어조 설정 조회")
async def get_chatbot_settings(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    setting = await crud_setting.get_setting_by_owner(db=db, owner=current_user)
    setting.tone_examples = json.loads(setting.tone_examples or '[]')
    return setting

@router.put("/settings", response_model=ChatbotSettingRead, summary="챗봇 어조 설정 수정")
async def update_chatbot_settings(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings_in: ChatbotSettingUpdate
):
    db_setting = await crud_setting.get_setting_by_owner(db=db, owner=current_user)
    updated_setting = await crud_setting.update_setting(db=db, db_obj=db_setting, obj_in=settings_in)
    updated_setting.tone_examples = json.loads(updated_setting.tone_examples or '[]')
    return updated_setting

# --- Public Chat Endpoint ---

@router.post("/public/{user_email}", summary="공개 챗봇에게 질문")
async def ask_public_chatbot(
    user_email: str,
    question: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
):
    owner = await crud_user.get_user_by_email(db=db, email=user_email)
    if not owner:
        raise HTTPException(status_code=404, detail="Chatbot owner not found.")

    settings = await crud_setting.get_setting_by_owner(db=db, owner=owner)
    tone_examples = json.loads(settings.tone_examples or '[]')

    inputs = {"question": question, "tone_examples": tone_examples}
    result = await agent_service.agent_executor.ainvoke(inputs)
    
    return {"answer": result.get("generation")}

