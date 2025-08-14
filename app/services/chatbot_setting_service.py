from fastapi import Depends

from app.models.chatbot_setting import ChatbotSetting
from app.models.user import User
from app.crud.chatbot_setting_crud import ChatbotSettingCRUD
from app.schemas.chatbot_setting_schema import ChatbotSettingUpdate


class ChatbotSettingService:
    def __init__(self, crud: ChatbotSettingCRUD = Depends()):
        self.crud = crud

    async def get_settings(self, *, current_user: User) -> ChatbotSetting:
        setting = await self.crud.get_chatbot_setting_by_user(user=current_user)
        return setting

    async def update_settings(
        self, *, settings_in: ChatbotSettingUpdate, current_user: User
    ) -> ChatbotSetting:
        db_setting = await self.crud.get_chatbot_setting_by_user(user=current_user)
        updated_setting = await self.crud.update_setting(
            db_obj=db_setting, obj_in=settings_in
        )
        return updated_setting
