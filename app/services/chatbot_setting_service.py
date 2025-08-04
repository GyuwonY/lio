from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chatbot_setting import ChatbotSetting
from app.models.user import User
from app.crud.chatbot_setting import ChatbotSettingCRUD
from app.schemas.chatbot_setting import ChatbotSettingUpdate
from app.models.chatbot_setting import ChatbotSetting


class ChatbotSettingService:
    def __init__(self, crud: ChatbotSettingCRUD):
        self.crud = crud

    async def get_settings(
        self, db: AsyncSession, *, current_user: User
    ) -> ChatbotSetting:
        setting = await self.crud.get_chatbot_setting_by_user(
            db=db, user=current_user
        )

        return setting

    async def update_settings(
        self, db: AsyncSession, *, settings_in: ChatbotSettingUpdate, current_user: User
    ) -> ChatbotSetting:
        db_setting = await self.crud.get_chatbot_setting_by_user(
            db=db, user=current_user
        )
        updated_setting = await self.crud.update_setting(
            db=db, db_obj=db_setting, obj_in=settings_in
        )
        
        return updated_setting
    