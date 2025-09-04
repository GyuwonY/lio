from typing import List, Optional
import uuid
import json
from fastapi import Depends, HTTPException, status
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from app.crud.chat_message_crud import ChatMessageCRUD
from app.crud.chat_session_crud import ChatSessionCRUD
from app.schemas.chat_message_schema import ChatMessageCreate, GraphStateQuery
from app.crud.portfolio_crud import PortfolioCRUD
from app.crud.qna_crud import QnACRUD
from app.crud.user_crud import UserCRUD
from app.schemas.llm_schema import LLMChatAnswer
from app.schemas.portfolio_item_schema import PortfolioItemLLMInput
from app.schemas.qna_schema import QnALLMInput
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

from app.services.chat_session_service import ChatSessionService
from app.schemas.chat_session_schema import ConversationTurn


class GraphState(BaseModel):
    session_id: str
    input: str
    portfolio_id: uuid.UUID
    context: List[ConversationTurn] = Field(default_factory=list)
    graph_state_queries: List[GraphStateQuery] = Field(default_factory=list)
    portfolio_item_ids: List[uuid.UUID] = Field(default_factory=list)
    portfolio_items: List[PortfolioItemLLMInput] = Field(default_factory=list)
    qnas: List[QnALLMInput] = Field(default_factory=list)
    chat_message: Optional[LLMChatAnswer] = None


class ChatMessageService:
    def __init__(
        self,
        portfolio_crud: PortfolioCRUD = Depends(),
        qna_crud: QnACRUD = Depends(),
        user_crud: UserCRUD = Depends(),
        chat_message_crud: ChatMessageCRUD = Depends(),
        chat_session_crud: ChatSessionCRUD = Depends(),
        llm_service: LLMService = Depends(),
        rag_service: RAGService = Depends(),
        session_service: ChatSessionService = Depends(),
    ):
        self.portfolio_crud = portfolio_crud
        self.qna_crud = qna_crud
        self.user_crud = user_crud
        self.chat_message_crud = chat_message_crud
        self.chat_session_crud = chat_session_crud
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.session_service = session_service

        workflow = StateGraph(GraphState)

        workflow.add_node("get_context_from_session", self.get_context_from_session)
        workflow.add_node("generate_queries_node", self.generate_queries_node)
        workflow.add_node("embed_queries", self.embed_queries)
        workflow.add_node("retrieve_portfolio_items", self.retrieve_portfolio_items)
        workflow.add_node("retrieve_qnas", self.retrieve_qnas)
        workflow.add_node("generate_chat_message", self.generate_chat_message)
        workflow.add_node("save_chat", self.save_chat)
        workflow.add_node("update_context_in_session", self.update_context_in_session)

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

        graph_state_queries = [
            GraphStateQuery(query=query) for query in generated_queries
        ]

        return {"graph_state_queries": graph_state_queries}

    def should_embed_queries_node(self, state: GraphState):
        if state.graph_state_queries:
            return "embed_queries"
        else:
            return "generate_chat_message"

    async def embed_queries(self, state: GraphState):
        queries = [
            graph_state_query.query for graph_state_query in state.graph_state_queries
        ]
        embeddings = await self.rag_service.embed_queries(queries=queries)

        updated_queries = []
        for graph_state_query, embedding in zip(state.graph_state_queries, embeddings):
            updated_queries.append(
                GraphStateQuery(query=graph_state_query.query, embedding=embedding)
            )

        return {"graph_state_queries": updated_queries}

    async def retrieve_portfolio_items(self, state: GraphState):
        if not state.graph_state_queries:
            return {"portfolio_item_ids": [], "portfolio_items": []}

        embeddings = [
            graph_state_query.embedding
            for graph_state_query in state.graph_state_queries
            if graph_state_query.embedding
        ]
        if not embeddings:
            return {"portfolio_item_ids": [], "portfolio_items": []}

        portfolio_items = await self.portfolio_crud.search_portfolio_items_by_embedding(
            embeddings=embeddings, portfolio_id=state.portfolio_id
        )

        return {
            "portfolio_items": [
                PortfolioItemLLMInput(
                    type=item.type.value,
                    topic=item.topic,
                    start_date=item.start_date,
                    end_date=item.end_date,
                    content=item.content,
                    tech_stack=item.tech_stack,
                )
                for item in portfolio_items
            ],
            "portfolio_item_ids": [item.id for item in portfolio_items],
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

        portfolio_items_dump = [item.model_dump() for item in state.portfolio_items]
        qnas_dump = [qna.model_dump() for qna in state.qnas]

        portfolio_context = {
            "portfolio_items": portfolio_items_dump,
            "qnas": qnas_dump,
        }

        llm_chat_answer = await self.llm_service.generate_chat_answer(
            conversation_history=conversation_history,
            portfolio_context=json.dumps(portfolio_context, ensure_ascii=False),
            user_input=state.input,
        )

        return {"chat_message": llm_chat_answer}

    async def save_chat(self, state: GraphState):
        chat_session = await self.chat_session_crud.get_chat_session_by_session_id(
            session_id=state.session_id
        )
        if not chat_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found",
            )

        if not state.chat_message:
            return {}

        await self.chat_message_crud.create_chat_message(
            chat_session_id=chat_session.id,
            question=state.input,
            answer=state.chat_message.answer,
            type=state.chat_message.type,
        )

        return {}

    async def update_context_in_session(self, state: GraphState):
        current_context = state.context

        if not state.chat_message:
            return {}

        new_turn = ConversationTurn(
            input=state.input,
            answer=state.chat_message.answer,
        )
        current_context.append(new_turn)

        if len(current_context) > 10:
            summary_turns = current_context[:-3]
            recent_turns = current_context[-3:]

            history_to_summarize = "\n".join(
                [f"Human: {c.input}\nAI: {c.answer}" for c in summary_turns]
            )

            summary = await self.llm_service.summarize_conversation(
                conversation_history=history_to_summarize
            )

            summarized_turn = ConversationTurn(
                input="지난 대화 요약",
                answer=summary,
            )

            current_context = [summarized_turn] + recent_turns

        if len(current_context) > 20:
            current_context = current_context[-20:]

        await self.session_service.update_session(
            session_id=state.session_id,
            context=current_context,
        )

        return {}

    async def run_chat(self, chat_create: ChatMessageCreate, session_id: str) -> str:
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

        initial_state = GraphState(
            session_id=session_id,
            portfolio_id=portfolio.id,
            input=chat_create.question,
        )

        final_state = await self.graph.ainvoke(initial_state)
        return final_state["chat_message"].answer
