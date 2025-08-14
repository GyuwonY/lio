from typing import List, Dict, Any
from fastapi import Depends, HTTPException, status

from app.crud.portfolio_crud import PortfolioCRUD
from app.schemas.portfolio_schema import PortfolioCreate, PortfolioRead
from app.models.user import User
from app.models.portfolio import Portfolio
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService

class PortfolioService:
    def __init__(
        self,
        crud: PortfolioCRUD = Depends(),
        rag_service: RAGService = Depends(),
        llm_service: LLMService = Depends(),
    ):
        self.crud = crud
        self.rag_service = rag_service
        self.llm_service = llm_service

    async def create_portfolio(
        self, *, portfolio_in: PortfolioCreate, current_user: User
    ) -> Portfolio:
        items_data: List[Dict[str, Any]] = []
        source_type: str = ""
        source_identifier: str | None = None

        if portfolio_in.file_url:
            source_type = "file"
            source_identifier = portfolio_in.file_url
            try:
                # 1. GCS에서 PDF 텍스트 추출
                text = await self.rag_service.extract_text_from_gcs_pdf(gcs_url=source_identifier)
                if not text.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="PDF 파일에서 텍스트를 추출할 수 없습니다. 내용이 비어있거나 텍스트 레이어가 없는 이미지 파일일 수 있습니다.",
                    )
                
                # 2. LLM으로 텍스트 구조화
                items_data = await self.llm_service.structure_portfolio_from_text(text=text)

            except FileNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"GCS에서 파일을 찾을 수 없습니다: {source_identifier}",
                )
            except ValueError as e:
                 raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"PDF 처리 또는 LLM 응답 파싱 중 오류 발생: {e}",
                )

        elif portfolio_in.text_items:
            source_type = "text"
            items_data = [item.model_dump() for item in portfolio_in.text_items]
        
        if not items_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="포트폴리오로 생성할 데이터가 없습니다.",
            )

        # 3. 각 항목 임베딩
        embeddings = await self.rag_service.embed_portfolio_items(items_data=items_data)
        
        # 4. 임베딩 결과를 각 항목 데이터에 추가
        for i, item in enumerate(items_data):
            item['embedding'] = embeddings[i]

        # 5. CRUD를 통해 DB에 최종 저장
        created_portfolio = await self.crud.create_portfolio_with_items(
            user_id=current_user.id,
            source_type=source_type,
            source_identifier=source_identifier,
            items_data=items_data,
        )
        
        return created_portfolio

    async def get_user_portfolios(self, *, current_user: User) -> List[Portfolio]:
        """사용자의 모든 포트폴리오 목록을 조회합니다."""
        return await self.crud.get_portfolios_by_user(user_id=current_user.id)

    async def delete_portfolio(self, *, portfolio_id: int, current_user: User) -> None:
        """포트폴리오를 삭제합니다."""
        deleted = await self.crud.delete_portfolio(portfolio_id=portfolio_id, user_id=current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        return None