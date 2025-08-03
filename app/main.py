from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title="Lio-Agent API",
    description="LLM 에이전트 기반 챗봇 포트폴리오 서비스",
    version="0.1.0"
)

@app.get("/", tags=["Root"])
def read_root():
    """
    서버 상태를 확인하기 위한 기본 엔드포인트입니다.
    """
    return {"message": "Welcome to Lio-Agent API"}

# API v1 라우터를 앱에 포함시킵니다.
app.include_router(api_router, prefix=settings.API_V1_STR)

# 서버 시작 시 필요한 초기화 로직 (예: DB 테이블 생성)
@app.on_event("startup")
async def on_startup():
    from app.db.session import async_engine, Base
    from app.services.rag_service import create_weaviate_schema_if_not_exists
    
    # Import all models here to ensure they are registered with Base
    from app.models import user, portfolio, qna, setting

    async with async_engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # 개발 중 테이블 초기화 필요시 사용
        await conn.run_sync(Base.metadata.create_all)
    
    # Weaviate 스키마 생성은 동기 함수이므로 그대로 호출
    create_weaviate_schema_if_not_exists()
