from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from fastapi import Depends, HTTPException

from app.crud.portfolio import PortfolioCRUD
from app.schemas.portfolio import PortfolioCreate
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.rag_service import RAGService
from app.services.storage_service import StorageService


class PortfolioService:
    def __init__(
        self,
        crud: PortfolioCRUD = Depends(),
        rag_service: RAGService = Depends(),
        storage_service: StorageService = Depends(),
    ):
        self.crud = crud
        self.rag_service = rag_service
        self.storage_service = storage_service

    def generate_presigned_url(self, *, file_name: str, current_user: User) -> dict:
        """
        Generates a presigned URL for the client to upload a file to GCS.
        Does NOT create any database records.
        """
        upload_url, object_url = self.storage_service.generate_upload_url(
            user_id=current_user.id, file_name=file_name
        )
        return {"upload_url": upload_url, "file_path": object_url}

    async def create_portfolio(
        self, *, file_name: str, file_path: str, current_user: User
    ) -> Portfolio:
        """
        Creates a portfolio record in the database after the file has been uploaded.
        Then, triggers the RAG processing.
        """
        # 1. Create portfolio record
        portfolio_in = PortfolioCreate(file_name=file_name, file_path=file_path)
        db_portfolio = await self.crud.create_portfolio(
            portfolio_in=portfolio_in, user_id=current_user.id
        )

        # 2. Process and store the document for RAG
        file_extension = db_portfolio.file_name.split(".")[-1].lower()
        if file_extension not in ["pdf", "txt"]:
            # Even if we check on the client, double-check here
            raise HTTPException(
                status_code=400, detail="Unsupported file type for processing."
            )

        await self.rag_service.process_and_store_document(
            file_path=db_portfolio.file_path,  # Pass the GCS URL
            file_type=file_extension,
            metadata={
                "user_id": str(current_user.id),
                "portfolio_id": db_portfolio.id,
                "file_name": db_portfolio.file_name,
            },
        )

        return db_portfolio

    async def get_user_portfolios(self, *, current_user: User) -> List[Portfolio]:
        return await self.crud.get_portfolios_by_user(user_id=current_user.id)
