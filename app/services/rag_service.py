import asyncio
import aiofiles
from typing import List, Dict, Any

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import weaviate as weaviate_store
from langchain_openai import OpenAIEmbeddings

from app.db.session import weaviate_client

WEAVIATE_CLASS_NAME = "Portfolio"

async def process_and_store_document(file_path: str, file_type: str, metadata: Dict[str, Any]):
    """
    업로드된 파일(PDF, TXT)을 비동기적으로 처리하여 Weaviate에 저장합니다.
    """
    # Langchain의 로더들은 대부분 동기적으로 작동하므로, 비동기 이벤트 루프를 차단하지 않도록
    # asyncio.to_thread를 사용하여 별도 스레드에서 실행합니다.
    def load_docs():
        if file_type == "pdf":
            loader = PyPDFLoader(file_path)
        elif file_type == "txt":
            loader = TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        return loader.load()

    documents = await asyncio.to_thread(load_docs)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(documents)

    for doc in split_docs:
        doc.metadata.update(metadata)

    embeddings = OpenAIEmbeddings() 
    
    # from_documents 역시 동기 함수이므로 to_thread 사용
    await asyncio.to_thread(
        weaviate_store.Weaviate.from_documents,
        client=weaviate_client,
        documents=split_docs,
        embedding=embeddings,
        index_name=WEAVIATE_CLASS_NAME,
        text_key="text",
    )

def create_weaviate_schema_if_not_exists():
    """
    Weaviate에 Portfolio 클래스(스키마)가 없으면 생성합니다. (동기 함수 유지)
    """
    if not weaviate_client.schema.exists(WEAVIATE_CLASS_NAME):
        schema = {
            "class": WEAVIATE_CLASS_NAME,
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {"model": "ada", "type": "text"}
            },
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "owner_id", "dataType": ["int"]},
                {"name": "portfolio_id", "dataType": ["int"]},
                {"name": "file_name", "dataType": ["string"]},
            ]
        }
        weaviate_client.schema.create_class(schema)
