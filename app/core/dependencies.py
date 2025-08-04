from fastapi import Depends
import weaviate

from app.services.auth_service import AuthService
from app.crud.user import UserCRUD
from app.services.agent_service import AgentService
from app.services.chatbot_setting_service import ChatbotSettingService
from app.crud.chatbot_setting import ChatbotSettingCRUD
from app.services.portfolio_service import PortfolioService
from app.crud.portfolio import PortfolioCRUD
from app.services.rag_service import RAGService
from app.services.qna_service import QnAService
from app.crud.qna import QnACRUD
from app.services.llm_service import LLMService
from app.db.session import weaviate_client


def get_weaviate_client() -> weaviate.Client:
    return weaviate_client


def get_auth_service() -> AuthService:
    return AuthService()


def get_user_crud() -> UserCRUD:
    return UserCRUD()


def get_chatbot_setting_crud() -> ChatbotSettingCRUD:
    return ChatbotSettingCRUD()


def get_chatbot_setting_service(
    crud: ChatbotSettingCRUD = Depends(get_chatbot_setting_crud),
) -> ChatbotSettingService:
    return ChatbotSettingService(crud=crud)


def get_agent_service(
    user_crud: UserCRUD = Depends(get_user_crud),
    chatbot_setting_service: ChatbotSettingService = Depends(
        get_chatbot_setting_service
    ),
) -> AgentService:
    return AgentService(
        user_crud=user_crud, chatbot_setting_service=chatbot_setting_service
    )


def get_portfolio_crud() -> PortfolioCRUD:
    return PortfolioCRUD()


def get_rag_service(
    client: weaviate.Client = Depends(get_weaviate_client),
) -> RAGService:
    return RAGService(weaviate_client=client)


def get_portfolio_service(
    crud: PortfolioCRUD = Depends(get_portfolio_crud),
    rag_service: RAGService = Depends(get_rag_service),
) -> PortfolioService:
    return PortfolioService(crud=crud, rag_service=rag_service)


def get_qna_crud() -> QnACRUD:
    return QnACRUD()


def get_llm_service(
    client: weaviate.Client = Depends(get_weaviate_client),
) -> LLMService:
    return LLMService(weaviate_client=client)


def get_qna_service(
    crud: QnACRUD = Depends(get_qna_crud),
    llm_service: LLMService = Depends(get_llm_service),
) -> QnAService:
    return QnAService(crud=crud, llm_service=llm_service)