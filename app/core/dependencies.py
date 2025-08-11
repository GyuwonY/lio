from app.db.session import weaviate_client


def get_weaviate_client():
    """Dependency to get the global Weaviate client instance."""
    return weaviate_client
