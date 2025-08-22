from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.prompts import (
    GENERATE_QNA_SYSTEM_PROMPT,
    GENERATE_QNA_USER_PROMPT,
    STRUCTURE_PORTFOLIO_SYSTEM_PROMPT,
    STRUCTURE_PORTFOLIO_USER_PROMPT,
)
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
        )
        self.generate_qna_model = ChatGoogleGenerativeAI(
            model=settings.GENERATE_QNA_LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
        )


    async def structure_portfolio_from_text(
        self, *, text: str
    ) -> LLMPortfolio:
        portfolio_parser = PydanticOutputParser(pydantic_object=LLMPortfolio)

        fix_parser = OutputFixingParser.from_llm(
            parser=portfolio_parser, llm=self.pdf_parsing_model
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", STRUCTURE_PORTFOLIO_SYSTEM_PROMPT),
                ("human", STRUCTURE_PORTFOLIO_USER_PROMPT),
            ]
        )

        prompt = prompt.partial(
            format_instructions=fix_parser.get_format_instructions()
        )

        chain = prompt | self.pdf_parsing_model | fix_parser

        parsed_portfolio = await chain.ainvoke({"text": text})
        return parsed_portfolio


    async def generate_qna_for_portfolio_item(
        self, *, item: PortfolioItem
    ) -> LLMQnAOutput:
        qna_parser = PydanticOutputParser(pydantic_object=LLMQnAOutput)

        fix_parser = OutputFixingParser.from_llm(
            parser=qna_parser, llm=self.generate_qna_model
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", GENERATE_QNA_SYSTEM_PROMPT),
                ("human", GENERATE_QNA_USER_PROMPT),
            ]
        )

        prompt = prompt.partial(
            format_instructions=fix_parser.get_format_instructions()
        )

        chain = prompt | self.generate_qna_model | fix_parser

        parsed_qna = await chain.ainvoke(
            {
                "topic": item.topic,
                "tech_stack": item.tech_stack,
                "content": item.content,
            }
        )
        return parsed_qna
