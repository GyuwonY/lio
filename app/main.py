from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import async_engine, Base, weaviate_client
from app.services.rag_service import RAGService
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Connect to Weaviate
    await weaviate_client.connect()

    # Create DB tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create Weaviate schema
    rag_service = RAGService(weaviate_client=weaviate_client)
    await rag_service.create_weaviate_schema_if_not_exists()

    yield

    # Shutdown
    # Close Weaviate connection
    await weaviate_client.close()


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

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    