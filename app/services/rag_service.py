import asyncio
import os
import tempfile
from typing import Any, List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from langchain_community.document_loaders import PyPDFLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.services.storage_service import StorageService
from app.db.session import get_db, get_embeddings_model
from app.models.portfolio import Portfolio
from app.models.portfolio_item import PortfolioItem
from app.models.qna import QnA


class RAGService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        storage_service: StorageService = Depends(),
        embeddings_model: GoogleGenerativeAIEmbeddings = Depends(get_embeddings_model),
    ):
        self.db = db
        self.storage_service = storage_service
        self.embeddings_model = embeddings_model

    async def extract_text_from_gcs_pdf(self, gcs_url: str) -> str:
        file_bytes = await self.storage_service.download_as_bytes(gcs_url)

        tmp_path = ""
        try:
            # Create a temporary file to store the PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                tmpfile.write(file_bytes)
                tmp_path = tmpfile.name

            # Load the PDF using UnstructuredPDFLoader's async method
            loader = PyPDFLoader(tmp_path)
            loop = asyncio.get_running_loop()
            documents = await loop.run_in_executor(None, loader.load)
            return " ".join([doc.page_content for doc in documents])
        finally:
            # Clean up the temporary file
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    async def embed_portfolio_items(
        self,
        items: List[PortfolioItem]
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
            texts = texts_to_embed, 
            output_dimensionality=768
        )

    async def similarity_search(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 5,
        search_type: str = "all",
    ) -> List[Any]:
        query_embedding = await self.embeddings_model.aembed_query(
            text = query_text,
            output_dimensionality=768
        )

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
