from typing import List
from fastapi import Depends, HTTPException, status
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from app.models.portfolio import Portfolio
from app.models.qna import QnA
from app.models.user import User
from app.schemas.chat_schema import ChatCreate
from app.crud.chat_crud import ChatCRUD
from app.crud.portfolio_crud import PortfolioCRUD
from app.crud.qna_crud import QnACRUD
from app.crud.user_crud import UserCRUD
from app.services.llm_service import LLMService
from app.core.prompts import (
    CONTEXTUALIZER_PROMPT,
    CHATBOT_PROMPT,
    NO_CONTEXT_CHATBOT_PROMPT,
)
from app.services.rag_service import RAGService


class GraphState(BaseModel):
    user: User
    ip: str
    input: str
    portfolio: Portfolio
    retrieved_qna: List[QnA] = Field(default_factory=list)
    filtered_context: str | None = None
    final_answer: str | None = None
    error: str | None  = None


class ChatService:
    def __init__(
        self,
        chat_crud: ChatCRUD = Depends(),
        portfolio_crud: PortfolioCRUD = Depends(),
        qna_crud: QnACRUD = Depends(),
        user_crud: UserCRUD = Depends(),
        llm_service: LLMService = Depends(),
        rag_service: RAGService = Depends(),
    ):
        self.chat_crud = chat_crud
        self.portfolio_crud = portfolio_crud
        self.qna_crud = qna_crud
        self.user_crud = user_crud
        self.llm_service = llm_service
        self.rag_service = rag_service

        workflow = StateGraph(GraphState)

        workflow.add_node("retrieve_portfolio", self.retrieve_portfolio)
        workflow.add_node("retrieve_qna", self.retrieve_qna)
        workflow.add_node("filter_context", self.filter_context)
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("save_chat", self.save_chat)

        workflow.set_entry_point("retrieve_portfolio")
        workflow.add_edge("retrieve_portfolio", "retrieve_qna")
        workflow.add_edge("retrieve_qna", "filter_context")
        workflow.add_edge("filter_context", "generate_answer")
        workflow.add_edge("generate_answer", "save_chat")
        workflow.add_edge("save_chat", END)

        self.graph = workflow.compile()
    
    async def retrieve_portfolio(self, state: GraphState):
        embedding = await self.rag_service.embed_query(query=state.input)
        portfolios = await self.portfolio_crud.search_portfolios_by_embedding(
            embedding=embedding, user_id=state.user.id
        )
        portfolio_ids = [p.id for p in portfolios]
        return {"portfolio_ids": portfolio_ids}

    async def retrieve_qna(self, state: GraphState):
        
        embedding = await self.rag_service.embed_query(query=user_input)
        qnas = await self.qna_crud.search_qnas_by_portfolio_ids_and_embedding(
            portfolio_ids=portfolio_ids, embedding=embedding, user_id=user_id
        )
        return {"retrieved_qna": [qna.model_dump() for qna in qnas]}

    def should_continue_to_filter(self, state: GraphState):
        if state["retrieved_qna"]:
            return "continue"
        else:
            return "end"

    async def filter_context(self, state: GraphState):
        user_input = state["user_input"]
        qnas = state["retrieved_qna"]
        context = "\n".join([f"Q: {q['question']}\nA: {q['answer']}" for q in qnas])
        
        prompt = CONTEXTUALIZER_PROMPT.format(question=user_input, context=context)
        filtered_context = await self.llm_service.generate_response(prompt)
        return {"filtered_context": filtered_context}

    async def generate_answer(self, state: GraphState):
        user_input = state["user_input"]
        filtered_context = state.get("filtered_context")

        if filtered_context:
            prompt = CHATBOT_PROMPT.format(
                question=user_input, context=filtered_context
            )
        else:
            prompt = NO_CONTEXT_CHATBOT_PROMPT.format(question=user_input)

        answer = await self.llm_service.generate_response(prompt)
        return {"final_answer": answer}

    async def save_chat(self, state: GraphState):
        print("---SAVE CHAT---")
        user_input = state["user_input"]
        final_answer = state["final_answer"]
        user_id = state["user_id"]
        
        user = await self.user_crud.get_user_by_id(user_id=user_id)
        if not user:
            # 실제 프로덕션에서는 더 견고한 예외 처리가 필요합니다.
            print(f"User with id {user_id} not found.")
            return {"error": f"User with id {user_id} not found."}

        chat_in = ChatCreate(question=user_input)
        await self.chat_crud.create_chat(
            chat_in=chat_in, user=user, answer=final_answer
        )
        return {}

    async def run_chat(self, chat_create: ChatCreate, ip: str):
        user = await self.user_crud.get_user_by_email(email=chat_create.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="존재하지 않는 유저",
            )
            
        portfolio = await self.portfolio_crud.get_portfolio_by_id(
            portfolio_id=chat_create.portfolio_id, 
            user_id=user.id
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="존재하지 않는 포트폴리오",
            )
        
        state = GraphState(
            user=user,
            ip=ip,
            portfolio=portfolio,
            input=chat_create.question,
        )

        final_state = await self.graph.ainvoke(state)
        return final_state
