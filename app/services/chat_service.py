from typing import List
import uuid
from fastapi import Depends, HTTPException, status
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from app.models.chat_session import ChatType
from app.models.portfolio import Portfolio
from app.models.portfolio_item import PortfolioItem
from app.models.qna import QnA
from app.models.user import User
from app.schemas.chat_schema import ChatCreate, GraphStateQuery
from app.crud.chat_crud import ChatCRUD
from app.crud.portfolio_crud import PortfolioCRUD
from app.crud.qna_crud import QnACRUD
from app.crud.user_crud import UserCRUD
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

from app.services.session_service import SessionService
from app.schemas.session_schema import ConversationTurn


class GraphState(BaseModel):
    user: User
    session_id: str
    input: str
    portfolio: Portfolio
    type: ChatType
    context: List[ConversationTurn] = Field(default_factory=list)
    graph_state_queries: List[GraphStateQuery] = Field(default_factory=list)
    portfolio_items: List[PortfolioItem] = Field(default_factory=list)
    retrieved_qna: List[QnA] = Field(default_factory=list)
    final_answer: str | None = None
    error: str | None = None


class ChatService:
    def __init__(
        self,
        chat_crud: ChatCRUD = Depends(),
        portfolio_crud: PortfolioCRUD = Depends(),
        qna_crud: QnACRUD = Depends(),
        user_crud: UserCRUD = Depends(),
        llm_service: LLMService = Depends(),
        rag_service: RAGService = Depends(),
        session_service: SessionService = Depends(),
    ):
        self.chat_crud = chat_crud
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
        workflow.add_node("generate_answer", self.generate_answer)
        workflow.add_node("save_chat", self.save_chat)
        workflow.add_node("update_context_in_session", self.update_context_in_session)

        workflow.set_entry_point("get_context_from_session")
        workflow.add_edge("generate_queries_node", "embed_queries")
        workflow.add_conditional_edges(
            "generate_queries_node", self.should_embed_queries_node
        )
        workflow.add_edge("embed_queries", "retrieve_portfolio_items")
        workflow.add_edge("retrieve_portfolio_items", "retrieve_qnas")
        workflow.add_edge("retrieve_qnas", "generate_answer")
        workflow.add_edge("generate_answer", "save_chat")
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
            return "generate_answer"

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
        
        return {"portfolio_items": portfolio_items}

    async def retrieve_qnas(self, state: GraphState):
        if not state.graph_state_queries:
            return {"retrieved_qna": []}
        embedding = state.graph_state_queries[0].embedding
        qnas = await self.qna_crud.search_qnas_by_portfolio_ids_and_embedding(
            portfolio_item_ids=state.portfolio_item_ids,
            embedding=embedding,
        )
        return {"retrieved_qna": [qna.model_dump() for qna in qnas]}

    async def generate_answer(self, state: GraphState):
        user_input = state.input
        filtered_context = state.get("retrieved_qna")

        if filtered_context:
            prompt = CHATBOT_PROMPT.format(
                question=user_input, context=filtered_context
            )
        else:
            prompt = NO_CONTEXT_CHATBOT_PROMPT.format(question=user_input)

        answer = await self.llm_service.generate_response(prompt)
        return {"final_answer": answer}

    async def save_chat(self, state: GraphState):
        chat_in = ChatCreate(
            question=state.input,
            email=state.user.email,
            portfolio_id=state.portfolio.id,
            type=state.type,
        )
        await self.chat_crud.create_chat(
            chat_in=chat_in,
            user=state.user,
            answer=state.final_answer,
            session_id=state.session_id,
            type=state.type,
        )
        return {}

    async def update_context_in_session(self, state: GraphState) -> dict:
        new_context_entry = ConversationTurn(
            input=state.input, answer=state.final_answer
        )
        await self.session_service.update_session_context(
            session_id=state.session_id, new_context=new_context_entry
        )
        return {}

    async def run_chat(self, chat_create: ChatCreate, session_id: str):
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
            type=chat_create.type,
        )

        final_state = await self.graph.ainvoke(state)
        return final_state