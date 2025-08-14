from fastapi import APIRouter, Depends

from app.schemas.chatbot_setting_schema import ChatbotSettingRead, ChatbotSettingUpdate
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.chatbot_setting_service import ChatbotSettingService

router = APIRouter()


@router.get("/tone", response_model=ChatbotSettingRead, summary="챗봇 어조 설정 조회")
async def get_chatbot_settings(
    current_user: User = Depends(get_current_user),
    service: ChatbotSettingService = Depends(),
):
    return await service.get_settings(current_user=current_user)


@router.put("/tone", response_model=ChatbotSettingRead, summary="챗봇 어조 설정 수정")
async def update_chatbot_settings(
    service: ChatbotSettingService = Depends(),
    current_user: User = Depends(get_current_user),
    *,
    settings_in: ChatbotSettingUpdate,
):
    return await service.update_settings(
        settings_in=settings_in, current_user=current_user
    )
