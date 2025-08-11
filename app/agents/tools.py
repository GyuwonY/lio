from langchain_weaviate import WeaviateVectorStore
from weaviate.client import WeaviateAsyncClient
from weaviate.classes.query import Filter

from app.services.rag_service import WEAVIATE_CLASS_NAME as PORTFOLIO_CLASS

QNA_CLASS = "ConfirmedQnA"


def create_user_retrievers(client: WeaviateAsyncClient, user_id: int):
    """
    Create retrievers scoped to a specific user ID using Weaviate v4 API.

    Args:
        client: An active weaviate.WeaviateAsyncClient instance.
        user_id: The ID of the user to filter data for.

    Returns:
        A tuple containing the portfolio retriever and QnA retriever.
    """
    # Weaviate v4 filter using Filter class
    user_filter = Filter.by_property("user_id").equal(user_id)

    # Use the modern WeaviateVectorStore from langchain_weaviate
    portfolio_vectorstore = WeaviateVectorStore(
        client=client,
        index_name=PORTFOLIO_CLASS,
        text_key="text",
    )
    qna_vectorstore = WeaviateVectorStore(
        client=client,
        index_name=QNA_CLASS,
        text_key="text",
    )

    # Create retrievers with the user-specific filter
    # The filter is passed inside search_kwargs
    portfolio_retriever = portfolio_vectorstore.as_retriever(
        search_kwargs={"filters": user_filter}
    )
    qna_retriever = qna_vectorstore.as_retriever(
        search_kwargs={"filters": user_filter}
    )

    return portfolio_retriever, qna_retriever