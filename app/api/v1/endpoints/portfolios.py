import tempfile
import os
import aiofiles
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.portfolio import PortfolioCreate, PortfolioRead
from app.crud import portfolio as crud_portfolio
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services import rag_service

router = APIRouter()

@router.post("/", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...)
):
    """
    새로운 포트폴리오를 업로드합니다. (PDF 또는 TXT 파일)
    """
    if file.size > 30 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds 30MB limit.")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["pdf", "txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    tmp_path = None
    try:
        # aiofiles를 사용하여 비동기적으로 임시 파일 생성 및 쓰기
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
            content = await file.read()
            await tmp.write(content)
            tmp_path = tmp.name

        # 1. DB에 메타데이터 저장
        portfolio_in = PortfolioCreate(file_name=file.filename)
        db_portfolio = await crud_portfolio.create_portfolio(
            db=db, portfolio_in=portfolio_in, owner_id=current_user.id
        )

        # 2. Weaviate에 문서 내용 저장 (RAG)
        await rag_service.process_and_store_document(
            file_path=tmp_path,
            file_type=file_extension,
            metadata={
                "owner_id": current_user.id,
                "portfolio_id": db_portfolio.id,
                "file_name": file.filename,
            }
        )
        
        return db_portfolio

    except Exception as e:
        # TODO: 트랜잭션 롤백 처리 필요
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/", response_model=List[PortfolioRead])
async def read_portfolios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자의 모든 포트폴리오 목록을 조회합니다.
    """
    return await crud_portfolio.get_portfolios_by_owner(db=db, owner_id=current_user.id)
