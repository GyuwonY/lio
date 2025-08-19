from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.models.portfolio_item import PortfolioItemType


# Pydantic 모델 정의
class PortfolioItemPydantic(BaseModel):
    type: PortfolioItemType = Field(
        description="항목 유형 (INTRODUCTION, EXPERIENCE, PROJECT, SKILLS, EDUCATION, CONTACT 중 하나)"
    )
    topic: Optional[str] = Field(None, description="회사명, 프로젝트명 등 항목의 주제")
    start_date: Optional[date] = Field(
        None,
        description="업무 또는 프로젝트의 시작일 DD가 없는 경우엔 01로 대체 ex) YYYY-MM-01",
    )
    end_date: Optional[date] = Field(
        None,
        description="업무 또는 프로젝트의 종료일 DD가 없는 경우엔 01로 대체 ex) YYYY-MM-01",
    )
    content: str = Field(
        description="항목의 요약되지 않은 원본 내용, 줄의 공백과 줄바꿈은 한줄로 변경합니다."
    )


class PortfolioPydantic(BaseModel):
    items: List[PortfolioItemPydantic]


STRUCTURE_PORTFOLIO_PROMPT = """
당신은 HR 전문가입니다. 주어진 포트폴리오 원본 텍스트에서 정보를 추출하고 구조화해주세요.

{format_instructions}

**포트폴리오 원본 텍스트:**
---
{text}
---
"""

class LLMService:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True,
        )
        self.parser = PydanticOutputParser(pydantic_object=PortfolioPydantic)

    async def structure_portfolio_from_text(
        self, text: str
    ) -> List[PortfolioItemPydantic]:
        """LLM을 사용하여 텍스트에서 구조화된 포트폴리오 항목들을 추출합니다."""
        prompt = ChatPromptTemplate.from_template(
            template=STRUCTURE_PORTFOLIO_PROMPT,
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )

        chain = prompt | self.model | self.parser

        response = await chain.ainvoke({"text": text})

        return response.items
