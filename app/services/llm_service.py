import json
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain.output_parsers import OutputFixingParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.core.prompts import (
    GENERATE_QNA_SYSTEM_PROMPT,
    GENERATE_QNA_USER_PROMPT,
    STRUCTURE_PORTFOLIO_SYSTEM_PROMPT,
    STRUCTURE_PORTFOLIO_USER_PROMPT,
    VECTOR_QUERY_GENERATOR_SYSTEM_PROMPT,
    VECTOR_QUERY_GENERATOR_USER_PROMPT,
    GENERATE_CHAT_ANSWER_SYSTEM_PROMPT,
    GENERATE_CHAT_ANSWER_USER_PROMPT,
    SUMMARIZE_CONVERSATION_SYSTEM_PROMPT,
    SUMMARIZE_CONVERSATION_USER_PROMPT,
)
from app.models.portfolio_item import PortfolioItem
from app.schemas.llm_schema import (
    LLMPortfolio,
    LLMQnAOutput,
    LLMSplitQueries,
    LLMChatAnswer,
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
            temperature=0.8,
        )
        self.query_generation_model = ChatGoogleGenerativeAI(
            model=settings.QUERY_GENERATION_LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
            convert_system_message_to_human=True,
        )
        self.chat_model = ChatGoogleGenerativeAI(
            model=settings.CHAT_LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.8,
            convert_system_message_to_human=True,
        )
        self.summarize_model = ChatGoogleGenerativeAI(
            model=settings.SUMMARIZE_LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True,
        )

    async def structure_portfolio_from_text(self, *, text: str) -> LLMPortfolio:
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
            format_instructions=portfolio_parser.get_format_instructions(), text=text
        )

        chain = prompt | self.pdf_parsing_model | fix_parser

        parsed_portfolio = await chain.ainvoke({})
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
            format_instructions=qna_parser.get_format_instructions(),
            topic=item.topic,
            tech_stack=item.tech_stack,
            content=item.content,
        )

        chain = prompt | self.generate_qna_model | fix_parser

        parsed_qna = await chain.ainvoke({})
        return parsed_qna

    async def generate_queries(self, *, context: str, user_input: str) -> List[str]:
        parser = PydanticOutputParser(pydantic_object=LLMSplitQueries)

        fix_parser = OutputFixingParser.from_llm(
            parser=parser, llm=self.query_generation_model
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", VECTOR_QUERY_GENERATOR_SYSTEM_PROMPT),
                ("human", VECTOR_QUERY_GENERATOR_USER_PROMPT),
            ]
        )

        prompt = prompt.partial(
            format_instructions=parser.get_format_instructions(),
            conversation_history=json.dumps(context, ensure_ascii=False),
            user_input=user_input,
        )

        chain = prompt | self.query_generation_model | fix_parser

        response = await chain.ainvoke({})
        return response.queries

    async def generate_chat_answer(
        self, *, conversation_history: str, portfolio_context: str, user_input: str
    ) -> LLMChatAnswer:
        parser = PydanticOutputParser(pydantic_object=LLMChatAnswer)

        fix_parser = OutputFixingParser.from_llm(parser=parser, llm=self.chat_model)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", GENERATE_CHAT_ANSWER_SYSTEM_PROMPT),
                ("human", GENERATE_CHAT_ANSWER_USER_PROMPT),
            ]
        )

        prompt = prompt.partial(
            format_instructions=parser.get_format_instructions(),
            conversation_history=conversation_history,
            portfolio_context=portfolio_context,
            user_input=user_input,
        )

        chain = prompt | self.chat_model | fix_parser

        response = await chain.ainvoke({})
        return response.answer

    async def summarize_conversation(self, *, conversation_history: str) -> str:
        parser = StrOutputParser()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SUMMARIZE_CONVERSATION_SYSTEM_PROMPT),
                ("user", SUMMARIZE_CONVERSATION_USER_PROMPT),
            ]
        )

        prompt = prompt.partial(
            conversation_history=conversation_history,
        )

        chain = prompt | self.summarize_model | parser

        response = await chain.ainvoke({})
        return response
