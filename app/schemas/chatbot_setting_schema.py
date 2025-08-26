import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ChatbotSettingBase(BaseModel):
    tone_examples: Optional[List[str]] = None


class ChatbotSettingUpdate(ChatbotSettingBase):
    pass


class ChatbotSettingRead(ChatbotSettingBase):
    id: uuid.UUID
    user_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
