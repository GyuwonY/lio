from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.chat_message import ChatMessageType
from app.models.portfolio_item import PortfolioItemType


class LLMQnA(BaseModel):
    question: str = Field(description="항목에 대한 예상 질문")
    answer: str = Field(description="질문에 대한 답변")


class LLMQnAOutput(BaseModel):
    qnas: List[LLMQnA]


class LLMPortfolioItem(BaseModel):
    type: PortfolioItemType = Field(
        description="항목 유형. 반드시 'INTRODUCTION', 'EXPERIENCE', 'PROJECT', 'SKILLS', 'EDUCATION', 'CONTACT' 중 하나여야 함"
    )
    topic: Optional[str] = Field(
        None, description="회사명, 프로젝트명, 학교명 등 항목의 주제"
    )
    start_date: Optional[date] = Field(
        None, description="시작일. YYYY-MM-DD 형식. DD 정보가 없으면 01로 설정."
    )
    end_date: Optional[date] = Field(
        None,
        description="종료일. YYYY-MM-DD 형식. DD 정보가 없으면 01로 설정. 진행 중(현재, 재직 중 등)인 경우 null",
    )
    content: str = Field(
        description="항목의 요약되지 않은 원본 내용. 줄바꿈과 연속 공백은 하나의 공백으로 정제하고, 파싱 오류로 생긴 무의미한 문자는 제거해야 함"
    )
    tech_stack: Optional[List[str]] = Field(
        None, description="명시적으로 나열된 기술 스택만 추출. 없는 경우 null"
    )


class LLMPortfolio(BaseModel):
    items: List[LLMPortfolioItem]


class LLMSplitQueries(BaseModel):
    queries: List[str]


class LLMChatAnswer(BaseModel):
    type: ChatMessageType = Field(
        description="항목 유형. 반드시 'TECH','PERSONAL','EDUCATION','SUGGEST','CONTACT','ETC' 중 하나여야 함"
    )
    answer: str = Field(description="질문에 대한 응답")
