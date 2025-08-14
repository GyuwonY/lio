from typing import List
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from app.services.rag_service import RAGService


class RAGServiceRetriever(BaseRetriever):
    """
    A custom retriever that uses our RAGService to fetch documents.
    """

    rag_service: RAGService
    user_id: int
    search_type: str  # "portfolio" or "qna"
    top_k: int = 4

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Asynchronously gets relevant documents from the RAGService.
        This is the synchronous wrapper required by LangChain's BaseRetriever.
        """
        # BaseRetriever's get_relevant_documents is synchronous,
        # so we need a way to call our async method.
        # The retriever interface in LangChain is becoming more async-friendly,
        # but for now, we might need a bridge if the calling context is sync.
        # Let's assume for now the context (like an agent) can handle `ainvoke`.
        # The `_get_relevant_documents` is the sync version.
        # We will implement the async version `_aget_relevant_documents`.
        raise NotImplementedError(
            "RAGServiceRetriever does not support synchronous retrieval."
        )

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        """
        Asynchronously gets relevant documents from the RAGService.
        """
        results = await self.rag_service.similarity_search(
            user_id=self.user_id,
            query_text=query,
            top_k=self.top_k,
            search_type=self.search_type,
        )

        documents = []
        for item in results:
            page_content = ""
            metadata = {"user_id": self.user_id}
            if hasattr(item, "file_name"):  # Portfolio
                # For portfolios, we might not have the full text in the DB anymore.
                # The "document" could be the file name or a summary.
                # Here, we'll just use the file_name as content for simplicity.
                page_content = f"Portfolio: {item.file_name}"
                metadata["type"] = "portfolio"
                metadata["portfolio_id"] = item.id
            elif hasattr(item, "question"):  # QnA
                page_content = f"Q: {item.question}\nA: {item.answer}"
                metadata["type"] = "qna"
                metadata["qna_id"] = item.id
            
            documents.append(Document(page_content=page_content, metadata=metadata))

        return documents


def create_user_retrievers(rag_service: RAGService, user_id: int):
    """
    Create retrievers scoped to a specific user ID using RAGService.

    Args:
        rag_service: An instance of RAGService.
        user_id: The ID of the user to filter data for.

    Returns:
        A tuple containing the portfolio retriever and QnA retriever.
    """
    portfolio_retriever = RAGServiceRetriever(
        rag_service=rag_service, user_id=user_id, search_type="portfolio"
    )
    qna_retriever = RAGServiceRetriever(
        rag_service=rag_service, user_id=user_id, search_type="qna"
    )

    return portfolio_retriever, qna_retriever
