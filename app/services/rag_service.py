# app/services/rag_service.py

import asyncio
import os
import tempfile
from typing import Any, List, Dict

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.services.storage_service import StorageService
from app.db.session import get_db
from app.models.portfolio import Portfolio
from app.models.portfolio_item import PortfolioItem
from app.models.qna import QnA


class RAGService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        storage_service: StorageService = Depends(),
    ):
        self.db = db
        self.storage_service = storage_service
        
        self.embeddings_model = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
        )

    async def extract_text_from_gcs_pdf(self, gcs_url: str) -> str:
        file_bytes = await self.storage_service.download_as_bytes(gcs_url)
        
        tmp_path = ""
        try:
            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                tmpfile.write(file_bytes)
                tmp_path = tmpfile.name

            # Load the PDF from the temporary file path
            loader = PyPDFLoader(tmp_path)
            documents = await asyncio.to_thread(loader.load)
            return " ".join([doc.page_content for doc in documents])
        finally:
            # Clean up the temporary file
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def embed_portfolio_items(self, items_data: List[Dict[str, Any]]) -> List[List[float]]:
        texts_to_embed = []
        for item in items_data:
            full_text = f"유형: {item['item_type']}\n"
            if item.get('topic'):
                full_text += f"주제: {item['topic']}\n"
            if item.get('period'):
                full_text += f"기간: {item['period']}\n"
            full_text += f"내용: {item['content']}"
            texts_to_embed.append(full_text)
        if not texts_to_embed:
            return []
        return await self.embeddings_model.aembed_documents(texts_to_embed)

    async def similarity_search(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 5,
        search_type: str = "all",
    ) -> List[Any]:
        query_embedding = await self.embeddings_model.aembed_query(query_text)

        results = []
        if search_type in ["portfolio", "all"]:
            portfolio_results = await self.db.execute(
                select(PortfolioItem)
                .join(Portfolio)
                .filter(Portfolio.user_id == user_id)
                .order_by(PortfolioItem.embedding.l2_distance(query_embedding))
                .limit(top_k)
            )
            results.extend(portfolio_results.scalars().all())

        if search_type in ["qna", "all"]:
            # QnA 검색은 기존 로직 유지
            qna_results = await self.db.execute(
                select(QnA)
                .filter(QnA.user_id == user_id)
                .order_by(QnA.embedding.l2_distance(query_embedding))
                .limit(top_k)
            )
            results.extend(qna_results.scalars().all())

        return results[:top_k]
