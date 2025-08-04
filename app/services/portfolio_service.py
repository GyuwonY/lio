import os
import aiofiles
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.crud.portfolio import PortfolioCRUD
from app.schemas.portfolio import PortfolioCreate
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.rag_service import RAGService


class PortfolioService:
    def __init__(self, crud: PortfolioCRUD, rag_service: RAGService):
        self.crud = crud
        self.rag_service = rag_service

    async def get_user_portfolios(
        self, db: AsyncSession, *, current_user: User
    ) -> List[Portfolio]:
        return await self.crud.get_portfolios_by_user(db=db, user_id=current_user.id)

    async def create_portfolio(
        self, db: AsyncSession, *, file: UploadFile, current_user: User
    ) -> Portfolio:
        if file.size > 30 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File size exceeds 30MB limit.")

        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ["pdf", "txt"]:
            raise HTTPException(status_code=400, detail="Unsupported file type.")

        tmp_path = None
        try:
            async with aiofiles.tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_extension}"
            ) as tmp:
                content = await file.read()
                await tmp.write(content)
                tmp_path = tmp.name

            portfolio_in = PortfolioCreate(file_name=file.filename)
            db_portfolio = await self.crud.create_portfolio(
                db=db, portfolio_in=portfolio_in, user_id=current_user.id
            )

            await self.rag_service.process_and_store_document(
                file_path=tmp_path,
                file_type=file_extension,
                metadata={
                    "user_id": str(current_user.id),
                    "portfolio_id": db_portfolio.id,
                    "file_name": file.filename,
                },
            )

            return db_portfolio

        except Exception as e:
            # TODO: 트랜잭션 롤백 처리 필요
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
