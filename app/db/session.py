from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from weaviate.client import WeaviateAsyncClient
from weaviate.connect import ConnectionParams

from app.core.config import settings

# 1. SQLAlchemy (MySQL) 비동기 설정
# ---------------------------------
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


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# 2. Weaviate 비동기 클라이언트 설정
# ---------------------------------

weaviate_client = WeaviateAsyncClient(
    connection_params=ConnectionParams.from_params(
        http_host=settings.WEAVIATE_HOST,
        http_port=settings.WEAVIATE_PORT,
        http_secure=True,
        grpc_host=settings.WEAVIATE_HOST,
        grpc_port=50051,  # Default gRPC port
        grpc_secure=True,
    )
)
