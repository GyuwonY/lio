import json
from typing import List, Dict, Any

from fastapi import Depends
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

# RAGService에서 프롬프트를 이곳으로 이동
STRUCTURE_PORTFOLIO_PROMPT = """
당신은 HR 전문가입니다. 주어진 포트폴리오 원본 텍스트에서 다음 JSON 스키마에 따라 정보를 추출하고 구조화해주세요.

**JSON 스키마:**
```json
{{
    "items": [
        {{
            "item_type": "소개|경력|프로젝트|기술스택|학력 및 교육",
            "topic": "회사명, 프로젝트명, 기술 이름 등 (해당하는 경우)",
            "period": "업무 기간, 프로젝트 기간 등 (해당하는 경우)",
            "content": "구체적인 내용, 역할, 성과 등"
        }}
    ]
}}
```

**추출 규칙:**
- 각 항목은 `item_type` 중 하나로 분류되어야 합니다.
- '경력'의 `topic`은 회사명, '프로젝트'의 `topic`은 프로젝트명입니다.
- '소개', '기술스택', '학력 및 교육'은 `topic`이나 `period`가 없을 수 있습니다.
- `content`는 각 항목의 핵심 내용을 요약하여 담아주세요.
- 주어진 텍스트에서 정보를 찾을 수 없는 경우, 해당 필드는 누락하거나 `null`로 설정하세요.
- 최종 결과는 반드시 JSON 형식이어야 합니다.

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
            convert_system_message_to_human=True
        )

    async def structure_portfolio_from_text(self, text: str) -> List[Dict[str, Any]]:
        """LLM을 사용하여 텍스트에서 구조화된 포트폴리오 항목들을 추출합니다."""
        prompt = ChatPromptTemplate.from_template(STRUCTURE_PORTFOLIO_PROMPT)
        chain = prompt | self.model | StrOutputParser()

        response_str = await chain.ainvoke({"text": text})
        
        try:
            json_part = response_str.split("```json")[1].split("```")[0]
            structured_data = json.loads(json_part)
        except Exception:
            try:
                structured_data = json.loads(response_str)
            except json.JSONDecodeError:
                raise ValueError("LLM의 응답을 JSON으로 파싱하는데 실패했습니다.")

        return structured_data.get("items", [])
