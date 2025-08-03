from sqlalchemy import Column, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.db.session import Base

class ChatbotSetting(Base):
    __tablename__ = "chatbot_settings"

    id = Column(Integer, primary_key=True, index=True)
    
    # 어조 예시 (여러 개를 JSON이나 구분자로 저장할 수 있음)
    tone_examples = Column(Text, nullable=True) 
    
    owner_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    owner = relationship("User", back_populates="chatbot_setting")

# User 모델에 chatbot_setting 관계 추가
from app.models.user import User
User.chatbot_setting = relationship("ChatbotSetting", uselist=False, back_populates="owner")
