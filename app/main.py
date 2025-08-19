from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import async_engine, Base
import uvicorn
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Create DB tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Lio-Agent API",
    description="LLM 에이전트 기반 챗봇 포트폴리오 서비스",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to Lio-Agent API"}


app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
