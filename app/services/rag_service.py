import asyncio
import os
import tempfile
from typing import List

from fastapi import Depends

from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.services.storage_service import StorageService
from app.models.portfolio_item import PortfolioItem
from app.models.qna import QnA
from app.core.config import settings


async def get_embeddings_model():
    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )


class RAGService:
    def __init__(
        self,
        storage_service: StorageService = Depends(),
        embeddings_model: GoogleGenerativeAIEmbeddings = Depends(get_embeddings_model)
    ):
        self.storage_service = storage_service
        self.embeddings_model = embeddings_model

    async def extract_text_from_gcs_pdf(self, gcs_url: str) -> str:
        file_bytes = await self.storage_service.download_as_bytes(gcs_url)

        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                tmpfile.write(file_bytes)
                tmp_path = tmpfile.name

            loader = PyPDFLoader(tmp_path)
            loop = asyncio.get_running_loop()
            documents = await loop.run_in_executor(None, loader.load)
            return " ".join([doc.page_content for doc in documents])
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def embed_portfolio_items(
        self, items: List[PortfolioItem]
    ) -> List[List[float]]:
        texts_to_embed = []
        for item in items:
            full_text = f"type: {item.type}\n"
            if item.topic:
                full_text += f"topic: {item.topic}\n"
            if item.start_date:
                full_text += f"start_date: {item.start_date}\n"
            if item.end_date:
                full_text += f"end_date: {item.end_date}\n"
            full_text += f"content: {item.content}"
            texts_to_embed.append(full_text)
        if not texts_to_embed:
            return []
        return await self.embeddings_model.aembed_documents(
            texts=texts_to_embed, output_dimensionality=768
        )

    async def embed_qnas(self, qnas: List[QnA]) -> List[List[float]]:
        texts_to_embed = []
        for qna in qnas:
            full_text = f"question: {qna.question}\n answer: {qna.answer}"
            texts_to_embed.append(full_text)
        if not texts_to_embed:
            return []
        return await self.embeddings_model.aembed_documents(
            texts=texts_to_embed, output_dimensionality=768
        )

    async def embed_queries(self, *, queries: List[str]) -> List[List[float]]:
        return await self.embeddings_model.aembed_documents(
            texts=queries, output_dimensionality=768
        )
