from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class ChatbotSettingBase(BaseModel):
    """공통 챗봇 설정 필드"""
    tone_examples: Optional[List[str]] = None

class ChatbotSettingUpdate(ChatbotSettingBase):
    """챗봇 설정 수정을 위한 스키마"""
    pass

class ChatbotSettingRead(ChatbotSettingBase):
    """챗봇 설정 조회를 위한 스키마 (API 응답용)"""
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
