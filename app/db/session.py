from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import redis.asyncio as redis
from app.core.config import settings

async_engine = create_async_engine(
    settings.DATABASE_URL, pool_pre_ping=True, echo=False
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
Base = declarative_base()

redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

async def get_redis_client():
    return redis_client

async def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )
