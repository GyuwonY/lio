from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.prompts import GENERATE_QNA_PROMPT, STRUCTURE_PORTFOLIO_PROMPT
from app.models.portfolio_item import PortfolioItem
from app.schemas.llm_schema import (
    LLMPortfolio,
    LLMQnAOutput,
)


class LLMService:
    def __init__(self):
        self.pdf_parsing_model = ChatGoogleGenerativeAI(
            model=settings.PDF_PARSING_LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True,
        )
        self.generate_qna_model = ChatGoogleGenerativeAI(
            model=settings.GENERATE_QNA_LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            convert_system_message_to_human=True,
        )

    async def structure_portfolio_from_text(
        self, *, text: str
    ) -> str:
        portfolio_parser = PydanticOutputParser(pydantic_object=LLMPortfolio)

        prompt = ChatPromptTemplate.from_template(
            template=STRUCTURE_PORTFOLIO_PROMPT,
            partial_variables={
                "format_instructions": portfolio_parser.get_format_instructions()
            },
        )

        chain = prompt | self.pdf_parsing_model | JsonOutputParser()
        response_json_str = await chain.ainvoke({"text": text})
        return response_json_str

    async def generate_qna_for_portfolio_item(self, *, item: PortfolioItem) -> str:
        """LLM을 사용하여 단일 포트폴리오 항목에 대한 QnA 세트를 생성합니다."""

        qna_parser = PydanticOutputParser(pydantic_object=LLMQnAOutput)
        prompt = ChatPromptTemplate.from_template(
            template=GENERATE_QNA_PROMPT,
            partial_variables={
                "format_instructions": qna_parser.get_format_instructions()
            },
        )

        chain = prompt | self.generate_qna_model | JsonOutputParser()
        response_json_str = await chain.ainvoke(
            {
                "topic": item.topic,
                "tech_stack": item.tech_stack,
                "content": item.content,
            }
        )
        return response_json_str
