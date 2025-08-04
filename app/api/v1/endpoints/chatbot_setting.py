from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chatbot_setting import ChatbotSettingRead, ChatbotSettingUpdate
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.chatbot_setting_service import ChatbotSettingService
from app.core.dependencies import get_chatbot_setting_service
from app.db.session import get_db

router = APIRouter()


@router.get(
    "/tone", response_model=ChatbotSettingRead, summary="챗봇 어조 설정 조회"
)
async def get_chatbot_settings(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: ChatbotSettingService = Depends(get_chatbot_setting_service),
):
    return await service.get_settings(db=db, current_user=current_user)


@router.put(
    "/tone", response_model=ChatbotSettingRead, summary="챗봇 어조 설정 수정"
)
async def update_chatbot_settings(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    settings_in: ChatbotSettingUpdate,
    service: ChatbotSettingService = Depends(get_chatbot_setting_service),
):
    return await service.update_settings(
        db=db, settings_in=settings_in, current_user=current_user
    )
