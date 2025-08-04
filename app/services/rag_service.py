import asyncio
from typing import Dict, Any
import os

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import weaviate as weaviate_store
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import weaviate

from app.core.config import settings

os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY
WEAVIATE_CLASS_NAME = "Portfolio"

class RAGService:
    

    def __init__(self, weaviate_client: weaviate.Client):
        self.client = weaviate_client
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    async def process_and_store_document(
        self, file_path: str, file_type: str, metadata: Dict[str, Any]
    ):
        def load_docs():
            if file_type == "pdf":
                loader = PyPDFLoader(file_path)
            elif file_type == "txt":
                loader = TextLoader(file_path, encoding="utf-8")
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            return loader.load()

        documents = await asyncio.to_thread(load_docs)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )
        split_docs = text_splitter.split_documents(documents)

        for doc in split_docs:
            doc.metadata.update(metadata)

        await asyncio.to_thread(
            weaviate_store.Weaviate.from_documents,
            client=self.client,
            documents=split_docs,
            embedding=self.embeddings,
            index_name=WEAVIATE_CLASS_NAME,
            text_key="text",
        )

    def create_weaviate_schema_if_not_exists(self):
        if not self.client.schema.exists(WEAVIATE_CLASS_NAME):
            schema = {
                "class": WEAVIATE_CLASS_NAME,
                "vectorizer": "text2vec-google",
                "moduleConfig": {
                    "text2vec-google": {"model": "gemini-pro", "type": "text"}
                },
                "properties": [
                    {"name": "text", "dataType": ["text"]},
                    {"name": "user_id", "dataType": ["int"]},
                    {"name": "portfolio_id", "dataType": ["int"]},
                    {"name": "file_name", "dataType": ["string"]},
                ],
            }
            self.client.schema.create_class(schema)
