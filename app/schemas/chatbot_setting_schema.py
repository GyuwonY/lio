from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ChatbotSettingBase(BaseModel):
    tone_examples: Optional[List[str]] = None


class ChatbotSettingUpdate(ChatbotSettingBase):
    pass


class ChatbotSettingRead(ChatbotSettingBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
