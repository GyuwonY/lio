from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import json

from app.models.setting import ChatbotSetting
from app.schemas.setting import ChatbotSettingUpdate
from app.models.user import User

async def get_setting_by_owner(db: AsyncSession, *, owner: User) -> ChatbotSetting:
    """
    사용자의 챗봇 설정을 비동기적으로 조회합니다. 없으면 기본값으로 생성합니다.
    """
    result = await db.execute(
        select(ChatbotSetting).filter(ChatbotSetting.owner_id == owner.id)
    )
    setting = result.scalars().first()
    
    if not setting:
        setting = ChatbotSetting(owner_id=owner.id, tone_examples=json.dumps([]))
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
    return setting

async def update_setting(db: AsyncSession, *, db_obj: ChatbotSetting, obj_in: ChatbotSettingUpdate) -> ChatbotSetting:
    """
    챗봇 설정을 비동기적으로 수정합니다.
    """
    if obj_in.tone_examples is not None:
        db_obj.tone_examples = json.dumps(obj_in.tone_examples)
    
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
