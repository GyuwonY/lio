import asyncio
from typing import Dict, Any
from urllib.parse import urlparse

from langchain_community.document_loaders.gcs_file import GCSFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from weaviate.client import WeaviateAsyncClient
from weaviate.classes.config import Property, DataType, Configure
from fastapi import Depends

from app.core.config import settings
from app.core.dependencies import get_weaviate_client

WEAVIATE_CLASS_NAME = "Portfolio"


class RAGService:
    def __init__(
        self, weaviate_client: WeaviateAsyncClient = Depends(get_weaviate_client), 
    ):
        self.client = weaviate_client
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )

    async def process_and_store_document(
        self, file_path: str, file_type: str, metadata: Dict[str, Any]
    ):
        # Parse the GCS URL to get bucket and blob name
        parsed_url = urlparse(file_path)
        if parsed_url.scheme != "gs":
            raise ValueError("File path must be a GCS URI (gs://...)")
        bucket_name = parsed_url.netloc
        blob_name = parsed_url.path.lstrip("/")

        # GCSFileLoader is synchronous, so we run it in a separate thread.
        loader = GCSFileLoader(
            project_name=settings.GCP_PROJECT_ID,
            bucket=bucket_name,
            blob=blob_name,
        )
        documents = await asyncio.to_thread(loader.load)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )
        split_docs = text_splitter.split_documents(documents)

        # Add additional metadata to each split document
        for doc in split_docs:
            doc.metadata.update(metadata)

        # Use the native async batch insertion with Weaviate v4 method
        collection = self.client.collections.get(WEAVIATE_CLASS_NAME)
        
        # Prepare a list of objects for batch insertion
        objects_to_insert = [
            {"text": doc.page_content, **doc.metadata} for doc in split_docs
        ]

        # Use collection.data.insert_many for batch import
        if objects_to_insert:
            await collection.data.insert_many(objects_to_insert)

    async def create_weaviate_schema_if_not_exists(self):
        exists = await self.client.collections.exists(WEAVIATE_CLASS_NAME)
        if not exists:
            async with self.client:
                await self.client.collections.create(
                name=WEAVIATE_CLASS_NAME,
                properties=[
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="user_id", data_type=DataType.INT),
                    Property(name="portfolio_id", data_type=DataType.INT),
                    Property(name="file_name", data_type=DataType.TEXT),
                ],
                vectorizer_config=Configure.Vectorizer.text2vec_google(
                    project_id=settings.GCP_PROJECT_ID, model_id="gemini-embedding-001"
                ),
            )
