from fastapi import Depends
from weaviate.client import WeaviateAsyncClient

from app.crud.user import UserCRUD
from app.services.chatbot_setting_service import ChatbotSettingService
from app.agents.tools import create_user_retrievers
from app.agents.graph import create_agent_graph
from app.core.dependencies import get_weaviate_client


class AgentService:
    def __init__(
        self,
        user_crud: UserCRUD = Depends(),
        chatbot_setting_service: ChatbotSettingService = Depends(),
        weaviate_client: WeaviateAsyncClient = Depends(get_weaviate_client),
    ):
        self.user_crud = user_crud
        self.chatbot_setting_service = chatbot_setting_service
        self.weaviate_client = weaviate_client
        # Create the reusable agent graph when the service is initialized
        self.agent_executor = create_agent_graph()

    async def ask_question(self, *, user_email: str, question: str) -> dict:
        """
        Handles the business logic of asking a question to the agent.
        1. Fetches the user and their chatbot settings.
        2. Creates user-specific retrievers.
        3. Invokes the agent with the question, settings, and user-specific retrievers.
        4. Returns the generated answer.
        """
        user = await self.user_crud.get_user_by_email(email=user_email)
        if not user:
            return {"error": "Chatbot user not found."}

        settings = await self.chatbot_setting_service.get_settings(current_user=user)

        tone_examples = settings.tone_examples if settings else []

        # Create retrievers scoped to the specific user for this request
        portfolio_retriever, qna_retriever = create_user_retrievers(
            client=self.weaviate_client, user_id=user.id
        )

        # Prepare inputs for the agent, including the user-specific retrievers
        inputs = {
            "question": question,
            "tone_examples": tone_examples,
            "portfolio_retriever": portfolio_retriever,
            "qna_retriever": qna_retriever,
        }

        result_state = await self.agent_executor.ainvoke(inputs)

        return {"answer": result_state.get("generation")}
