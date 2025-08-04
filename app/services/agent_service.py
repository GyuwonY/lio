from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import StrOutputParser
from langchain_community.vectorstores.weaviate import Weaviate
from langchain.tools.retriever import create_retriever_tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import weaviate_client
from app.services.rag_service import WEAVIATE_CLASS_NAME as PORTFOLIO_CLASS
from app.services.chatbot_setting_service import ChatbotSettingService
from app.crud.user import UserCRUD

QNA_CLASS = "ConfirmedQnA"

class AgentService:
    def __init__(
        self,
        user_crud: UserCRUD,
        chatbot_setting_service: ChatbotSettingService,
    ):
        self.user_crud = user_crud
        self.chatbot_setting_service = chatbot_setting_service

        # --- 1. Tools ---
        portfolio_vectorstore = Weaviate(
            client=weaviate_client, index_name=PORTFOLIO_CLASS, text_key="text"
        )
        qna_vectorstore = Weaviate(
            client=weaviate_client, index_name=QNA_CLASS, text_key="text"
        )
        self.portfolio_retriever = portfolio_vectorstore.as_retriever()
        self.qna_retriever = qna_vectorstore.as_retriever()

        portfolio_tool = create_retriever_tool(
            self.portfolio_retriever,
            "portfolio_search",
            "Search for information in the user's portfolio.",
        )
        qna_tool = create_retriever_tool(
            self.qna_retriever,
            "qna_search",
            "Search for answers in the user's confirmed QnA list.",
        )
        self.tools = [portfolio_tool, qna_tool]

        # --- 2. Graph ---
        workflow = StateGraph(self.AgentState)
        workflow.add_node("retrieve", self.retrieve_context)
        workflow.add_node("generate", self.generate_answer)
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        self.agent_executor = workflow.compile()

    # --- 2. Agent State ---
    class AgentState(TypedDict):
        question: str
        generation: str
        context: Annotated[List[str], operator.add]
        tone_examples: List[str]

    # --- 3. Nodes ---
    async def retrieve_context(self, state):
        question = state["question"]
        portfolio_docs, qna_docs = await asyncio.gather(
            self.portfolio_retriever.ainvoke(question),
            self.qna_retriever.ainvoke(question),
        )
        context = [doc.page_content for doc in portfolio_docs + qna_docs]
        return {"context": context}

    async def generate_answer(self, state):
        question = state["question"]
        context = state["context"]
        tone_examples = "\n".join(f"- {ex}" for ex in state["tone_examples"])

        prompt = ChatPromptTemplate.from_template(
            """당신은 'lio'라는 이름의 챗봇입니다. 사용자를 대신하여 방문자의 질문에 답변해야 합니다.
            주어진 컨텍스트와 아래 어조 예시를 참고하여 질문에 대해 친절하고 명확하게 답변해주세요.
            모르는 내용에 대해서는 솔직하게 모른다고 답변하세요.

            어조 예시:
            {tone_examples}

            컨텍스트:
            {context}

            질문: {question}

            답변:"""
        )
        llm = ChatOpenAI(model="gpt-4o")
        chain = prompt | llm | StrOutputParser()
        generation = await chain.ainvoke(
            {"context": context, "question": question, "tone_examples": tone_examples}
        )
        return {"generation": generation}

    async def ask_question(
        self,
        db: AsyncSession,
        *, 
        user_email: str,
        question: str
    ) -> dict:
        user = await self.user_crud.get_user_by_email(db=db, email=user_email)
        if not user:
            return {"error": "Chatbot user not found."}

        settings = await self.chatbot_setting_service.get_settings(
            db=db, current_user=user
        )

        inputs = {"question": question, "tone_examples": settings.tone_examples}
        result = await self.agent_executor.ainvoke(inputs)
        return {"answer": result.get("generation")}