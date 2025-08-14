from typing import List
from fastapi import Depends, HTTPException, status

from app.crud.portfolio_crud import PortfolioCRUD
from app.schemas.portfolio_schema import (
    PortfolioCreateFromText,
    PortfolioCreateWithPdf,
    PortfolioItemsUpdate,
    PortfolioConfirm,
)
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioSourceType, PortfolioStatus
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

    async def create_portfolio_from_text(
        self, *, portfolio_in: PortfolioCreateFromText, current_user: User
    ) -> Portfolio:
        """텍스트 입력을 받아 포트폴리오를 생성하고 바로 확정(CONFIRMED)합니다."""
        if not portfolio_in.text_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="포트폴리오로 생성할 데이터가 없습니다.",
            )

        items_data = [item.model_dump() for item in portfolio_in.text_items]
        
        # 1. 각 항목 임베딩
        embeddings = await self.rag_service.embed_portfolio_items(items_data=items_data)
        
        # 2. 임베딩 결과를 각 항목 데이터에 추가
        for i, item in enumerate(items_data):
            item['embedding'] = embeddings[i]

        # 3. CRUD를 통해 DB에 최종 저장
        created_portfolio = await self.crud.create_portfolio(
            user_id=current_user.id,
            source_type=PortfolioSourceType.TEXT,
            source_url=None,
            status=PortfolioStatus.CONFIRMED,
            items_data=items_data,
        )
        
        return created_portfolio

    async def create_portfolio_from_pdf(
        self, *, portfolio_in: PortfolioCreateWithPdf, current_user: User
    ) -> Portfolio:
        """PDF 파일에서 텍스트를 추출하고 구조화하여 PENDING 상태의 포트폴리오를 생성합니다."""
        try:
            # 1. GCS에서 PDF 텍스트 추출
            text = await self.rag_service.extract_text_from_gcs_pdf(gcs_url=portfolio_in.file_path)
            if not text.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF 파일에서 텍스트를 추출할 수 없습니다.",
                )
            
            # 2. LLM으로 텍스트 구조화
            structured_items = await self.llm_service.structure_portfolio_from_text(text=text)
            if not structured_items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="LLM이 텍스트를 구조화하지 못했습니다.",
                )

            items_data = [item.model_dump() for item in structured_items]

            # 3. CRUD를 통해 PENDING 상태로 저장 (임베딩 없음)
            created_portfolio = await self.crud.create_portfolio(
                user_id=current_user.id,
                source_type=PortfolioSourceType.PDF,
                source_url=portfolio_in.file_path,
                status=PortfolioStatus.PENDING,
                items_data=items_data,
            )
            return created_portfolio

        except FileNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GCS에서 파일을 찾을 수 없습니다: {portfolio_in.file_path}",
            )
        except ValueError as e:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF 처리 또는 LLM 응답 파싱 중 오류 발생: {e}",
            )

    async def confirm_portfolio(
        self, *, confirm_in: PortfolioConfirm, current_user: User
    ) -> Portfolio:
        """PENDING 상태의 포트폴리오를 CONFIRMED로 변경하고 임베딩을 저장합니다."""
        portfolio = await self.crud.get_portfolio_by_id(
            portfolio_id=confirm_in.portfolio_id, user_id=current_user.id
        )
        if not portfolio:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="포트폴리오를 찾을 수 없습니다.")
        
        if portfolio.status != PortfolioStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 확정된 포트폴리오입니다.")

        items_data = [
            {"item_type": item.item_type.value, "content": item.content}
            for item in portfolio.items
        ]
        
        # 1. 항목 내용 임베딩
        embeddings = await self.rag_service.embed_portfolio_items(items_data=items_data)
        
        # 2. CRUD를 통해 상태 및 임베딩 업데이트
        updated_portfolio = await self.crud.update_portfolio_status_and_items(
            portfolio_id=portfolio.id,
            user_id=current_user.id,
            embeddings=embeddings,
        )
        return updated_portfolio

    async def get_user_portfolios(self, *, current_user: User) -> List[Portfolio]:
        """사용자의 모든 포트폴리오 목록을 조회합니다."""
        return await self.crud.get_portfolios_by_user(user_id=current_user.id)

    async def update_portfolio_items(
        self, *, items_in: PortfolioItemsUpdate, current_user: User
    ) -> Portfolio:
        """포트폴리오 항목 목록을 업데이트합니다."""
        update_data_list = []
        
        # 임베딩을 다시 계산해야 하는 항목만 추립니다.
        items_to_re_embed = []
        for item_update in items_in.items:
            # content가 변경된 경우에만 임베딩을 다시 계산합니다.
            if item_update.content:
                items_to_re_embed.append(item_update.model_dump())
        
        # 임베딩 계산
        if items_to_re_embed:
            embeddings = await self.rag_service.embed_portfolio_items(items_data=items_to_re_embed)
            
            # 임베딩 결과를 딕셔너리로 만들어 id로 쉽게 찾을 수 있게 합니다.
            embedding_map = {item['id']: emb for item, emb in zip(items_to_re_embed, embeddings)}
        else:
            embedding_map = {}

        # 최종 업데이트 데이터를 준비합니다.
        for item_update in items_in.items:
            item_dict = item_update.model_dump(exclude_unset=True)
            
            # 새로 계산된 임베딩이 있으면 추가합니다.
            if item_update.id in embedding_map:
                item_dict['embedding'] = embedding_map[item_update.id]
            
            update_data_list.append(item_dict)

        if not update_data_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="수정할 내용이 없습니다.",
            )

        # CRUD를 통해 DB 업데이트
        updated_portfolio = await self.crud.update_portfolio_items(
            items_update_data=update_data_list,
            user_id=current_user.id,
        )
        return updated_portfolio

    async def delete_portfolio(self, *, portfolio_id: int, current_user: User) -> None:
        """포트폴리오를 삭제합니다."""
        deleted = await self.crud.delete_portfolio(portfolio_id=portfolio_id, user_id=current_user.id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
            )
        return None

    async def delete_portfolio_items(self, *, portfolio_item_ids: List[int], current_user: User) -> None:
            """포트폴리오를 삭제합니다."""
            deleted = await self.crud.delete_portfolio_items(portfolio_item_ids=portfolio_item_ids)
            if not deleted:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="삭제할 포트폴리오를 찾을 수 없거나 권한이 없습니다.",
                )
            return None