from typing import List
import uuid
import json
from fastapi import Depends, HTTPException, status
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from app.models.portfolio import Portfolio
from app.models.user import User
from app.schemas.chat_message_schema import ChatMessageCreate, GraphStateQuery
from app.crud.portfolio_crud import PortfolioCRUD
from app.crud.qna_crud import QnACRUD
from app.crud.user_crud import UserCRUD
from app.schemas.llm_schema import LLMChatAnswer
from app.schemas.portfolio_schema import PortfolioItemLLMInput
from app.schemas.qna_schema import QnALLMInput
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

from app.services.chat_session_service import ChatSessionService
from app.schemas.chat_session_schema import ConversationTurn


class GraphState(BaseModel):
    user: User
    session_id: str
    input: str
    portfolio: Portfolio
    context: List[ConversationTurn] = Field(default_factory=list)
    graph_state_queries: List[GraphStateQuery] = Field(default_factory=list)
    portfolio_item_ids: List[uuid.UUID] = Field(default_factory=list)
    portfolio_items: List[PortfolioItemLLMInput] = Field(default_factory=list)
    qnas: List[QnALLMInput] = Field(default_factory=list)
    chat_message: LLMChatAnswer | None = None


class ChatMessageService:
    def __init__(self,
        portfolio_crud: PortfolioCRUD = Depends(),
        qna_crud: QnACRUD = Depends(),
        user_crud: UserCRUD = Depends(),
        llm_service: LLMService = Depends(),
        rag_service: RAGService = Depends(),
        session_service: ChatSessionService = Depends(),
    ):
        self.portfolio_crud = portfolio_crud
        self.qna_crud = qna_crud
        self.user_crud = user_crud
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.session_service = session_service

        workflow = StateGraph(GraphState)

        workflow.add_node("get_context_from_session", self.get_context_from_session)
        workflow.add_node(
            "generate_queries_node", self.generate_queries_node
        )
        workflow.add_node("embed_queries", self.embed_queries)
        workflow.add_node("retrieve_portfolio_items", self.retrieve_portfolio_items)
        workflow.add_node("retrieve_qnas", self.retrieve_qnas)
        workflow.add_node("generate_chat_message", self.generate_chat_message)
        workflow.add_node("save_chat", self.save_chat)

        workflow.set_entry_point("get_context_from_session")
        workflow.add_edge("get_context_from_session", "generate_queries_node")
        workflow.add_conditional_edges(
            "generate_queries_node", self.should_embed_queries_node
        )
        workflow.add_edge("embed_queries", "retrieve_portfolio_items")
        workflow.add_edge("retrieve_portfolio_items", "retrieve_qnas")
        workflow.add_edge("retrieve_qnas", "generate_chat_message")
        workflow.add_edge("generate_chat_message", "save_chat")
        workflow.add_edge("save_chat", "update_context_in_session")
        workflow.add_edge("update_context_in_session", END)

        self.graph = workflow.compile()

    async def get_context_from_session(self, state: GraphState) -> dict:
        session_data = await self.session_service.get_session(state.session_id)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        return {"context": session_data.context or []}

    async def generate_queries_node(self, state: GraphState) -> dict:
        conversation_history = "\n".join(
            [f"Human: {c.input}\nAI: {c.answer}" for c in state.context]
        )

        generated_queries = await self.llm_service.generate_queries(
            context=conversation_history, user_input=state.input
        )
        
        graph_state_queries = [GraphStateQuery(
            query=query
        ) for query in generated_queries]
        
        return {"graph_state_queries": graph_state_queries}
    
    async def should_embed_queries_node(self, state: GraphState):
        if state.graph_state_queries:
            return "embed_queries"
        else:
            return "generate_chat_message"

    async def embed_queries(self, state: GraphState):
        queries = [
            graph_state_query.query for graph_state_query in state.graph_state_queries
        ]
        embeddings = await self.rag_service.embed_queries(queries=queries)

        for graph_state_query, embedding in zip(state.graph_state_queries, embeddings):
            graph_state_query.embedding = embedding

        return {"graph_state_queries": state.graph_state_queries}

    async def retrieve_portfolio_items(self, state: GraphState):
        if not state.graph_state_queries:
            return {"portfolio_item_ids": []}
        embeddings = [graph_state_query.embedding for graph_state_query in state.graph_state_queries]
        portfolio_items = await self.portfolio_crud.search_portfolio_items_by_embedding(embeddings=embeddings, portfolio_id=state.portfolio.id)
        
        return {
            "portfolio_items": [PortfolioItemLLMInput(
                type=item.type.value,
                topic=item.topic,
                start_date=item.start_date,
                end_date=item.end_date,
                content=item.content,
                tech_stack=item.tech_stack,
            ) for item in portfolio_items],
            "portfolio_item_ids": [item.id for item in portfolio_items]
        }

    async def retrieve_qnas(self, state: GraphState):
        if not state.graph_state_queries:
            return {"qnas": []}

        portfolio_item_ids = state.portfolio_item_ids
        embeddings = [
            query.embedding
            for query in state.graph_state_queries
            if query.embedding is not None
        ]

        retrieved_qnas = await self.qna_crud.search_qnas_by_embeddings(
            portfolio_item_ids=portfolio_item_ids, embeddings=embeddings
        )

        return {"qnas": retrieved_qnas}

    async def generate_chat_message(self, state: GraphState):
        conversation_history = "\n".join(
            [f"Human: {c.input}\nAI: {c.answer}" for c in state.context]
        )

        portfolio_context = {
            "portfolio_items": [item.model_dump() for item in state.portfolio_items],
            "qnas": [qna.model_dump() for qna in state.qnas],
        }
        
        llm_chat_answer = await self.llm_service.generate_chat_answer(
            conversation_history=conversation_history,
            portfolio_context=json.dumps(portfolio_context, ensure_ascii=False),
            user_input=state.input,
        )

        chat_message = LLMChatAnswer(
            answer=llm_chat_answer.answer,
            type=llm_chat_answer.type,
        )
        
        return {"chat_message": chat_message}

    async def save_chat(self, state: GraphState):
        
        return {}

    async def run_chat(self, chat_create: ChatMessageCreate, session_id: str):
        user = await self.user_crud.get_user_by_email(email=chat_create.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="존재하지 않는 유저",
            )

        portfolio = await self.portfolio_crud.get_portfolio_by_id(
            portfolio_id=chat_create.portfolio_id, user_id=user.id
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="존재하지 않는 포트폴리오",
            )

        state = GraphState(
            user=user,
            session_id=session_id,
            portfolio=portfolio,
            input=chat_create.question,
        )

        final_state = await self.graph.ainvoke(state)
        return final_state
