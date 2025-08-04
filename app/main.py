from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import async_engine, Base, weaviate_client
from app.services.rag_service import RAGService

# Import all models here to ensure they are registered with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with async_engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # 개발 중 테이블 초기화 필요시 사용
        await conn.run_sync(Base.metadata.create_all)

    # Weaviate 스키마 생성
    rag_service = RAGService(weaviate_client=weaviate_client)
    rag_service.create_weaviate_schema_if_not_exists()
    yield


app = FastAPI(
    title="Lio-Agent API",
    description="LLM 에이전트 기반 챗봇 포트폴리오 서비스",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to Lio-Agent API"}


app.include_router(api_router, prefix=settings.API_V1_STR)
